"""
Claude Vision API Integration

Analyze rendered images using Claude's multimodal capabilities
to validate scene composition and provide feedback.
"""

import os
import base64
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field


# Check for anthropic library
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@dataclass
class ValidationResult:
    """Result of a render validation."""
    success: bool
    matches_description: bool = False
    confidence: float = 0.0
    elements_found: List[str] = field(default_factory=list)
    elements_missing: List[str] = field(default_factory=list)
    quality_assessment: str = ""
    suggestions: List[str] = field(default_factory=list)
    raw_analysis: str = ""
    error_message: Optional[str] = None

    @property
    def needs_changes(self) -> bool:
        """Returns True if the render needs modifications."""
        return not self.matches_description or len(self.suggestions) > 0

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'matches_description': self.matches_description,
            'confidence': self.confidence,
            'elements_found': self.elements_found,
            'elements_missing': self.elements_missing,
            'quality_assessment': self.quality_assessment,
            'suggestions': self.suggestions,
            'needs_changes': self.needs_changes,
            'error_message': self.error_message,
        }


@dataclass
class ComparisonResult:
    """Result of comparing two renders."""
    success: bool
    images_similar: bool = False
    differences: List[str] = field(default_factory=list)
    preferred_image: Optional[int] = None  # 1 or 2
    preference_reason: str = ""
    raw_analysis: str = ""
    error_message: Optional[str] = None


def encode_image(image_path: Union[str, Path]) -> str:
    """
    Encode an image file as base64.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_media_type(image_path: Union[str, Path]) -> str:
    """
    Determine the media type for an image file.

    Args:
        image_path: Path to the image file

    Returns:
        MIME type string
    """
    path = Path(image_path)
    suffix = path.suffix.lower()

    media_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }

    return media_types.get(suffix, 'image/png')


def check_api_available() -> tuple:
    """
    Check if the Claude API is available.

    Returns:
        Tuple of (available: bool, message: str)
    """
    if not HAS_ANTHROPIC:
        return False, "anthropic library not installed. Install with: pip install anthropic"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "ANTHROPIC_API_KEY environment variable not set"

    return True, "API available"


def validate_render(
    image_path: Union[str, Path],
    scene_description: str,
    additional_criteria: Optional[List[str]] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 2048
) -> ValidationResult:
    """
    Validate a rendered image against a scene description.

    Args:
        image_path: Path to the rendered image
        scene_description: Description of expected scene content
        additional_criteria: Extra validation criteria to check
        model: Claude model to use
        max_tokens: Maximum response tokens

    Returns:
        ValidationResult with analysis
    """
    available, message = check_api_available()
    if not available:
        return ValidationResult(
            success=False,
            error_message=message
        )

    # Build the validation prompt
    criteria_text = ""
    if additional_criteria:
        criteria_text = "\n\nAdditional criteria to check:\n"
        for i, criterion in enumerate(additional_criteria, 1):
            criteria_text += f"{i}. {criterion}\n"

    prompt = f"""Analyze this 3D rendered image and validate it against the following scene description.

EXPECTED SCENE:
{scene_description}
{criteria_text}
Please evaluate the image and respond with a JSON object containing:

{{
    "matches_description": true/false,
    "confidence": 0.0-1.0 (how confident you are in your assessment),
    "elements_found": ["list of expected elements that are present"],
    "elements_missing": ["list of expected elements that are missing or incorrect"],
    "quality_assessment": "Brief assessment of lighting, composition, and visual quality",
    "suggestions": ["list of specific improvements needed, if any"]
}}

Respond ONLY with the JSON object, no other text."""

    try:
        client = anthropic.Anthropic()

        # Encode the image
        image_data = encode_image(image_path)
        media_type = get_media_type(image_path)

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        raw_response = response.content[0].text

        # Parse the JSON response
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                return ValidationResult(
                    success=True,
                    raw_analysis=raw_response,
                    error_message="Could not parse JSON response"
                )

        return ValidationResult(
            success=True,
            matches_description=data.get('matches_description', False),
            confidence=data.get('confidence', 0.0),
            elements_found=data.get('elements_found', []),
            elements_missing=data.get('elements_missing', []),
            quality_assessment=data.get('quality_assessment', ''),
            suggestions=data.get('suggestions', []),
            raw_analysis=raw_response
        )

    except Exception as e:
        return ValidationResult(
            success=False,
            error_message=str(e)
        )


def analyze_render(
    image_path: Union[str, Path],
    question: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024
) -> str:
    """
    Ask a specific question about a rendered image.

    Args:
        image_path: Path to the image
        question: Question to ask about the image
        model: Claude model to use
        max_tokens: Maximum response tokens

    Returns:
        Claude's response text
    """
    available, message = check_api_available()
    if not available:
        return f"Error: {message}"

    try:
        client = anthropic.Anthropic()

        image_data = encode_image(image_path)
        media_type = get_media_type(image_path)

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ]
        )

        return response.content[0].text

    except Exception as e:
        return f"Error: {str(e)}"


def compare_renders(
    image1_path: Union[str, Path],
    image2_path: Union[str, Path],
    comparison_criteria: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024
) -> ComparisonResult:
    """
    Compare two rendered images.

    Args:
        image1_path: Path to first image
        image2_path: Path to second image
        comparison_criteria: Specific aspects to compare
        model: Claude model to use
        max_tokens: Maximum response tokens

    Returns:
        ComparisonResult with analysis
    """
    available, message = check_api_available()
    if not available:
        return ComparisonResult(
            success=False,
            error_message=message
        )

    criteria_text = ""
    if comparison_criteria:
        criteria_text = f"\n\nFocus on: {comparison_criteria}"

    prompt = f"""Compare these two 3D rendered images (Image 1 and Image 2).
{criteria_text}
Respond with a JSON object:

{{
    "images_similar": true/false,
    "differences": ["list of notable differences between the images"],
    "preferred_image": 1 or 2 (which image is better quality/composition),
    "preference_reason": "brief explanation of why one image is preferred"
}}

Respond ONLY with the JSON object."""

    try:
        client = anthropic.Anthropic()

        image1_data = encode_image(image1_path)
        image2_data = encode_image(image2_path)
        media_type1 = get_media_type(image1_path)
        media_type2 = get_media_type(image2_path)

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Image 1:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type1,
                                "data": image1_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Image 2:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type2,
                                "data": image2_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        raw_response = response.content[0].text

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                return ComparisonResult(
                    success=True,
                    raw_analysis=raw_response,
                    error_message="Could not parse JSON response"
                )

        return ComparisonResult(
            success=True,
            images_similar=data.get('images_similar', False),
            differences=data.get('differences', []),
            preferred_image=data.get('preferred_image'),
            preference_reason=data.get('preference_reason', ''),
            raw_analysis=raw_response
        )

    except Exception as e:
        return ComparisonResult(
            success=False,
            error_message=str(e)
        )


def generate_scene_suggestions(
    scene_description: str,
    style_reference: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 2048
) -> Dict[str, Any]:
    """
    Generate detailed scene setup suggestions from a description.

    Args:
        scene_description: High-level scene description
        style_reference: Optional style reference (e.g., "Pixar style")
        model: Claude model to use
        max_tokens: Maximum response tokens

    Returns:
        Dictionary with detailed scene setup recommendations
    """
    available, message = check_api_available()
    if not available:
        return {'error': message}

    style_text = ""
    if style_reference:
        style_text = f"\n\nTarget style: {style_reference}"

    prompt = f"""Generate detailed 3D scene setup recommendations for this scene description:

SCENE DESCRIPTION:
{scene_description}
{style_text}
Provide a JSON response with:

{{
    "camera": {{
        "position": [x, y, z],
        "target": [x, y, z],
        "focal_length": mm,
        "notes": "explanation"
    }},
    "lighting": {{
        "type": "three_point/outdoor/studio",
        "key_position": [x, y, z],
        "key_intensity": value,
        "ambient_color": [r, g, b],
        "time_of_day": "if outdoor",
        "notes": "explanation"
    }},
    "objects": [
        {{
            "name": "object name",
            "type": "primitive type or description",
            "position": [x, y, z],
            "scale": [x, y, z],
            "material": {{
                "type": "principled/emission/etc",
                "color": [r, g, b, a],
                "roughness": 0-1,
                "metallic": 0-1
            }}
        }}
    ],
    "environment": {{
        "type": "gradient/hdri/solid",
        "colors": ["for gradient"],
        "notes": "explanation"
    }},
    "composition_notes": "overall composition advice",
    "render_settings": {{
        "samples": recommended,
        "resolution": [w, h],
        "notes": "any special render settings"
    }}
}}

Respond ONLY with the JSON object."""

    try:
        client = anthropic.Anthropic()

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw_response = response.content[0].text

        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                return json.loads(json_match.group())
            return {'raw_response': raw_response, 'error': 'Could not parse JSON'}

    except Exception as e:
        return {'error': str(e)}


class RenderValidator:
    """
    High-level render validation interface.

    Provides iterative validation with history tracking.
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the validator.

        Args:
            model: Claude model to use
        """
        self.model = model
        self.history: List[Dict[str, Any]] = []
        self.available, self.status = check_api_available()

    def validate(
        self,
        image_path: Union[str, Path],
        scene_description: str,
        **kwargs
    ) -> ValidationResult:
        """
        Validate a render and track in history.

        Args:
            image_path: Path to rendered image
            scene_description: Expected scene description
            **kwargs: Additional validation parameters

        Returns:
            ValidationResult
        """
        result = validate_render(
            image_path,
            scene_description,
            model=self.model,
            **kwargs
        )

        self.history.append({
            'image_path': str(image_path),
            'scene_description': scene_description,
            'result': result.to_dict(),
            'iteration': len(self.history) + 1
        })

        return result

    def get_improvement_prompt(self, result: ValidationResult) -> str:
        """
        Generate a prompt for improving the scene based on validation.

        Args:
            result: ValidationResult from validation

        Returns:
            Improvement prompt string
        """
        if result.matches_description and not result.suggestions:
            return "No improvements needed - render matches description."

        lines = ["Improvements needed:"]

        if result.elements_missing:
            lines.append("\nMissing elements:")
            for elem in result.elements_missing:
                lines.append(f"  - Add: {elem}")

        if result.suggestions:
            lines.append("\nSuggestions:")
            for suggestion in result.suggestions:
                lines.append(f"  - {suggestion}")

        return "\n".join(lines)

    def clear_history(self) -> None:
        """Clear validation history."""
        self.history = []

    def get_history_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of validation history."""
        return [
            {
                'iteration': h['iteration'],
                'matches': h['result']['matches_description'],
                'suggestions_count': len(h['result']['suggestions'])
            }
            for h in self.history
        ]
