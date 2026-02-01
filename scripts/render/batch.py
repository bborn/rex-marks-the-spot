"""
Batch Rendering Support

Run multiple render jobs sequentially or in parallel.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime

from .engine import RenderResult, RenderConfig, render_script, render_blend_file


@dataclass
class BatchJob:
    """Definition of a single batch render job."""
    name: str
    source: str  # Path to .py or .blend file
    output: str  # Output path
    samples: int = 128
    resolution: tuple = (1920, 1080)
    priority: int = 0  # Higher = run first
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'source': self.source,
            'output': self.output,
            'samples': self.samples,
            'resolution': self.resolution,
            'priority': self.priority,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
        }


@dataclass
class BatchResult:
    """Result of a batch render operation."""
    total_jobs: int
    completed: int
    failed: int
    total_time: float
    results: Dict[str, RenderResult] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'total_jobs': self.total_jobs,
            'completed': self.completed,
            'failed': self.failed,
            'total_time': self.total_time,
            'success_rate': self.completed / self.total_jobs if self.total_jobs > 0 else 0,
            'results': {k: v.to_dict() for k, v in self.results.items()},
        }


def render_scenes(
    scenes: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
    verbose: bool = True
) -> BatchResult:
    """
    Render multiple scenes sequentially.

    Args:
        scenes: List of scene definitions, each with:
            - 'script' or 'blend': Source file path
            - 'output': Output filename (or full path)
            - 'samples': Optional sample count
        output_dir: Base output directory (optional)
        verbose: Print progress

    Returns:
        BatchResult with all outcomes
    """
    start_time = time.time()
    results = {}
    completed = 0
    failed = 0

    for i, scene in enumerate(scenes):
        name = scene.get('name', f'scene_{i}')

        if verbose:
            print(f"\n[{i + 1}/{len(scenes)}] Rendering: {name}")

        # Determine source
        source = scene.get('script') or scene.get('blend')
        if not source:
            results[name] = RenderResult(
                success=False,
                error_message="No 'script' or 'blend' specified"
            )
            failed += 1
            continue

        # Determine output path
        output = scene.get('output', f'{name}.png')
        if output_dir and not os.path.isabs(output):
            output = os.path.join(output_dir, output)

        # Ensure output directory exists
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        # Create config
        config = RenderConfig(
            output_path=output,
            samples=scene.get('samples', 128),
            resolution=scene.get('resolution', (1920, 1080))
        )

        # Render
        if source.endswith('.blend'):
            result = render_blend_file(source, output, config, verbose=verbose)
        else:
            result = render_script(source, output, config=config, verbose=verbose)

        results[name] = result

        if result.success:
            completed += 1
            if verbose:
                print(f"  Completed in {result.render_time:.1f}s: {output}")
        else:
            failed += 1
            if verbose:
                print(f"  FAILED: {result.error_message}")

    total_time = time.time() - start_time

    return BatchResult(
        total_jobs=len(scenes),
        completed=completed,
        failed=failed,
        total_time=total_time,
        results=results
    )


def render_jobs(
    jobs: List[BatchJob],
    parallel: int = 1,
    progress_callback: Optional[Callable[[str, RenderResult], None]] = None,
    verbose: bool = True
) -> BatchResult:
    """
    Execute a batch of render jobs.

    Args:
        jobs: List of BatchJob objects
        parallel: Number of parallel renders (1 = sequential)
        progress_callback: Called after each job completes
        verbose: Print progress

    Returns:
        BatchResult with all outcomes
    """
    start_time = time.time()

    # Sort by priority (higher first) and check dependencies
    sorted_jobs = sorted(jobs, key=lambda j: -j.priority)

    results = {}
    completed_names = set()

    if parallel <= 1:
        # Sequential execution
        for i, job in enumerate(sorted_jobs):
            if verbose:
                print(f"\n[{i + 1}/{len(jobs)}] {job.name}")

            # Check dependencies
            if job.dependencies:
                missing = [d for d in job.dependencies if d not in completed_names]
                if missing:
                    result = RenderResult(
                        success=False,
                        error_message=f"Unmet dependencies: {missing}"
                    )
                    results[job.name] = result
                    if progress_callback:
                        progress_callback(job.name, result)
                    continue

            # Execute
            result = _execute_job(job, verbose)
            results[job.name] = result

            if result.success:
                completed_names.add(job.name)

            if progress_callback:
                progress_callback(job.name, result)
    else:
        # Parallel execution (dependencies handled in waves)
        remaining = list(sorted_jobs)

        while remaining:
            # Find jobs whose dependencies are met
            ready = []
            still_waiting = []

            for job in remaining:
                missing_deps = [d for d in job.dependencies if d not in completed_names]
                if not missing_deps:
                    ready.append(job)
                else:
                    still_waiting.append(job)

            if not ready:
                # No jobs can run - circular dependency or missing deps
                for job in still_waiting:
                    results[job.name] = RenderResult(
                        success=False,
                        error_message=f"Unmet dependencies: {job.dependencies}"
                    )
                break

            # Execute ready jobs in parallel
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {
                    executor.submit(_execute_job, job, verbose): job
                    for job in ready
                }

                for future in as_completed(futures):
                    job = futures[future]
                    result = future.result()
                    results[job.name] = result

                    if result.success:
                        completed_names.add(job.name)

                    if progress_callback:
                        progress_callback(job.name, result)

            remaining = still_waiting

    # Calculate statistics
    completed = sum(1 for r in results.values() if r.success)
    failed = len(results) - completed
    total_time = time.time() - start_time

    return BatchResult(
        total_jobs=len(jobs),
        completed=completed,
        failed=failed,
        total_time=total_time,
        results=results
    )


def _execute_job(job: BatchJob, verbose: bool) -> RenderResult:
    """Execute a single batch job."""
    config = RenderConfig(
        output_path=job.output,
        samples=job.samples,
        resolution=job.resolution
    )

    # Ensure output directory exists
    Path(job.output).parent.mkdir(parents=True, exist_ok=True)

    if job.source.endswith('.blend'):
        return render_blend_file(job.source, job.output, config, verbose=verbose)
    else:
        return render_script(job.source, job.output, config=config, verbose=verbose)


def render_animation_frames(
    source: str,
    output_pattern: str,
    start_frame: int,
    end_frame: int,
    samples: int = 128,
    parallel: int = 1,
    verbose: bool = True
) -> BatchResult:
    """
    Render animation frames as individual jobs.

    Args:
        source: Path to .py script or .blend file
        output_pattern: Output pattern with {frame} placeholder
        start_frame: First frame number
        end_frame: Last frame number
        samples: Render samples
        parallel: Number of parallel renders
        verbose: Print progress

    Returns:
        BatchResult with all frame outcomes
    """
    jobs = []

    for frame in range(start_frame, end_frame + 1):
        output = output_pattern.format(frame=frame, f=frame)

        jobs.append(BatchJob(
            name=f"frame_{frame:04d}",
            source=source,
            output=output,
            samples=samples,
            metadata={'frame': frame}
        ))

    return render_jobs(jobs, parallel=parallel, verbose=verbose)


def load_batch_config(config_path: str) -> List[BatchJob]:
    """
    Load batch job configuration from a JSON file.

    Args:
        config_path: Path to the JSON config file

    Returns:
        List of BatchJob objects
    """
    with open(config_path, 'r') as f:
        data = json.load(f)

    jobs = []
    for item in data.get('jobs', []):
        jobs.append(BatchJob(
            name=item.get('name', 'unnamed'),
            source=item['source'],
            output=item['output'],
            samples=item.get('samples', 128),
            resolution=tuple(item.get('resolution', [1920, 1080])),
            priority=item.get('priority', 0),
            dependencies=item.get('dependencies', []),
            metadata=item.get('metadata', {})
        ))

    return jobs


def save_batch_report(result: BatchResult, output_path: str) -> None:
    """
    Save batch render report to a JSON file.

    Args:
        result: BatchResult to save
        output_path: Path for the report file
    """
    report = result.to_dict()
    report['timestamp'] = datetime.now().isoformat()

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)


class BatchRenderer:
    """
    High-level batch rendering interface.

    Provides a convenient API for managing batch render jobs.
    """

    def __init__(self, output_dir: str = './renders'):
        """
        Initialize the batch renderer.

        Args:
            output_dir: Default output directory for renders
        """
        self.output_dir = output_dir
        self.jobs: List[BatchJob] = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def add_job(
        self,
        name: str,
        source: str,
        output: Optional[str] = None,
        **kwargs
    ) -> BatchJob:
        """
        Add a job to the batch.

        Args:
            name: Job name
            source: Path to .py script or .blend file
            output: Output path (None = auto-generate)
            **kwargs: Additional BatchJob parameters

        Returns:
            The created BatchJob
        """
        if output is None:
            output = os.path.join(self.output_dir, f"{name}.png")

        job = BatchJob(
            name=name,
            source=source,
            output=output,
            **kwargs
        )
        self.jobs.append(job)
        return job

    def add_from_config(self, config_path: str) -> List[BatchJob]:
        """
        Add jobs from a config file.

        Args:
            config_path: Path to JSON config

        Returns:
            List of added jobs
        """
        new_jobs = load_batch_config(config_path)
        self.jobs.extend(new_jobs)
        return new_jobs

    def run(
        self,
        parallel: int = 1,
        verbose: bool = True
    ) -> BatchResult:
        """
        Execute all queued jobs.

        Args:
            parallel: Number of parallel renders
            verbose: Print progress

        Returns:
            BatchResult
        """
        result = render_jobs(self.jobs, parallel=parallel, verbose=verbose)
        return result

    def clear(self) -> None:
        """Clear all queued jobs."""
        self.jobs = []
