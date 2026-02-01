/**
 * TaskYou Board Widget - Real-time Version
 * Fetches and displays a live task board from the TaskYou API
 * Polls every 2-3 seconds for real-time updates
 */

(function() {
    'use strict';

    // Configuration
    const API_BASE_URL = 'https://api.rexmarksthespot.com';
    const REFRESH_INTERVAL = 2500; // 2.5 seconds for real-time feel
    const OUTPUT_REFRESH_INTERVAL = 1500; // 1.5 seconds for output when viewing
    const MAX_TASKS_PER_COLUMN = 8;
    const OUTPUT_LINES = 30;

    // Column display configuration
    const COLUMN_CONFIG = {
        backlog: { icon: '\u{1F4CB}', label: 'Backlog', color: 'var(--color-text-muted, #6b7280)' },
        queued: { icon: '\u{23F3}', label: 'Queued', color: 'var(--color-accent, #f59e0b)' },
        processing: { icon: '\u{26A1}', label: 'In Progress', color: 'var(--color-primary, #3b82f6)' },
        blocked: { icon: '\u{1F6AB}', label: 'Blocked', color: '#ef4444' },
        done: { icon: '\u{2713}', label: 'Done', color: 'var(--color-secondary, #10b981)' }
    };

    // Task type icons
    const TYPE_ICONS = {
        code: '\u{1F4BB}',
        thinking: '\u{1F914}',
        research: '\u{1F50D}',
        design: '\u{1F3A8}',
        default: '\u{1F4DD}'
    };

    // State
    let refreshTimer = null;
    let outputRefreshTimer = null;
    let selectedTaskId = null;
    let isOutputModalOpen = false;
    let connectionStatus = 'connecting';
    let lastBoardData = null;

    /**
     * Initialize the TaskYou board widget
     */
    function initTaskYouBoard() {
        const container = document.getElementById('taskyou-board');
        if (!container) return;

        // Add required styles if not present
        injectStyles();

        // Initial render with loading state
        renderLoading(container);

        // Start fetching
        loadBoard();
        startAutoRefresh();

        // Handle visibility changes to pause/resume when tab is hidden
        document.addEventListener('visibilitychange', handleVisibilityChange);
    }

    /**
     * Inject CSS styles for the widget
     */
    function injectStyles() {
        if (document.getElementById('taskyou-board-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'taskyou-board-styles';
        styles.textContent = `
            .taskyou-board-container {
                background: var(--color-surface, #1a1a2e);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
            }

            .taskyou-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                flex-wrap: wrap;
                gap: 0.5rem;
            }

            .taskyou-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--color-text, #fff);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .taskyou-status {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                color: var(--color-text-muted, #9ca3af);
            }

            .taskyou-status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }

            .taskyou-status-dot.connected { background: #10b981; }
            .taskyou-status-dot.connecting { background: #f59e0b; }
            .taskyou-status-dot.error { background: #ef4444; animation: none; }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .taskyou-columns {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }

            .taskyou-column {
                background: var(--color-background, #0f0f1a);
                border-radius: 8px;
                padding: 1rem;
                min-height: 150px;
            }

            .taskyou-column[data-status="processing"] {
                border: 2px solid var(--color-primary, #3b82f6);
                box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
            }

            .taskyou-column-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.75rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid var(--color-border, #2d2d44);
            }

            .taskyou-column-icon {
                font-size: 1rem;
            }

            .taskyou-column-title {
                font-weight: 600;
                font-size: 0.875rem;
                color: var(--color-text, #fff);
                flex: 1;
            }

            .taskyou-column-count {
                background: var(--color-surface, #1a1a2e);
                color: var(--color-text-muted, #9ca3af);
                padding: 0.125rem 0.5rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 500;
            }

            .taskyou-tasks {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            .taskyou-task {
                background: var(--color-surface, #1a1a2e);
                border-radius: 6px;
                padding: 0.75rem;
                cursor: pointer;
                transition: transform 0.15s, box-shadow 0.15s;
                border: 1px solid transparent;
            }

            .taskyou-task:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                border-color: var(--color-border, #2d2d44);
            }

            .taskyou-task.active {
                border-color: var(--color-primary, #3b82f6);
                animation: task-pulse 2s infinite;
            }

            @keyframes task-pulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
                50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
            }

            .taskyou-task.completed {
                opacity: 0.7;
            }

            .taskyou-task-header {
                display: flex;
                align-items: flex-start;
                gap: 0.5rem;
            }

            .taskyou-task-icon {
                font-size: 1rem;
                line-height: 1.4;
            }

            .taskyou-task-content {
                flex: 1;
                min-width: 0;
            }

            .taskyou-task-title {
                font-size: 0.8125rem;
                font-weight: 500;
                color: var(--color-text, #fff);
                display: block;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .taskyou-task-age {
                font-size: 0.6875rem;
                color: var(--color-text-muted, #9ca3af);
                display: block;
                margin-top: 0.25rem;
            }

            .taskyou-task-id {
                font-size: 0.6875rem;
                color: var(--color-text-muted, #6b7280);
                background: var(--color-background, #0f0f1a);
                padding: 0.125rem 0.375rem;
                border-radius: 4px;
                font-family: monospace;
            }

            .taskyou-empty {
                color: var(--color-text-muted, #6b7280);
                font-size: 0.8125rem;
                text-align: center;
                padding: 1rem;
                font-style: italic;
            }

            .taskyou-more {
                color: var(--color-text-muted, #9ca3af);
                font-size: 0.75rem;
                text-align: center;
                padding: 0.5rem;
            }

            .taskyou-error {
                text-align: center;
                padding: 2rem;
                color: var(--color-text-muted, #9ca3af);
            }

            .taskyou-retry {
                margin-top: 1rem;
                padding: 0.5rem 1rem;
                background: var(--color-primary, #3b82f6);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.875rem;
            }

            .taskyou-retry:hover {
                opacity: 0.9;
            }

            .taskyou-loading {
                text-align: center;
                padding: 3rem;
                color: var(--color-text-muted, #9ca3af);
            }

            .taskyou-loading-spinner {
                width: 32px;
                height: 32px;
                border: 3px solid var(--color-border, #2d2d44);
                border-top-color: var(--color-primary, #3b82f6);
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            /* Output Modal */
            .taskyou-modal-overlay {
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.75);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                padding: 1rem;
            }

            .taskyou-modal {
                background: var(--color-surface, #1a1a2e);
                border-radius: 12px;
                width: 100%;
                max-width: 800px;
                max-height: 80vh;
                display: flex;
                flex-direction: column;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }

            .taskyou-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 1.5rem;
                border-bottom: 1px solid var(--color-border, #2d2d44);
            }

            .taskyou-modal-title {
                font-weight: 600;
                color: var(--color-text, #fff);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .taskyou-modal-close {
                background: none;
                border: none;
                color: var(--color-text-muted, #9ca3af);
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0.25rem;
                line-height: 1;
            }

            .taskyou-modal-close:hover {
                color: var(--color-text, #fff);
            }

            .taskyou-modal-body {
                flex: 1;
                overflow: auto;
                padding: 1rem 1.5rem;
            }

            .taskyou-output {
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
                font-size: 0.75rem;
                line-height: 1.6;
                color: var(--color-text, #e5e5e5);
                white-space: pre-wrap;
                word-break: break-word;
                background: var(--color-background, #0f0f1a);
                padding: 1rem;
                border-radius: 6px;
                max-height: 50vh;
                overflow: auto;
            }

            .taskyou-output-empty {
                color: var(--color-text-muted, #6b7280);
                font-style: italic;
                text-align: center;
                padding: 2rem;
            }

            .taskyou-modal-footer {
                padding: 0.75rem 1.5rem;
                border-top: 1px solid var(--color-border, #2d2d44);
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.75rem;
                color: var(--color-text-muted, #9ca3af);
            }

            .taskyou-live-indicator {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .taskyou-live-dot {
                width: 6px;
                height: 6px;
                background: #10b981;
                border-radius: 50%;
                animation: pulse 1.5s infinite;
            }
        `;
        document.head.appendChild(styles);
    }

    /**
     * Render loading state
     */
    function renderLoading(container) {
        container.innerHTML = `
            <div class="taskyou-board-container">
                <div class="taskyou-loading">
                    <div class="taskyou-loading-spinner"></div>
                    <div>Connecting to TaskYou...</div>
                </div>
            </div>
        `;
    }

    /**
     * Fetch board data and render it
     */
    async function loadBoard() {
        const container = document.getElementById('taskyou-board');
        if (!container) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/board`);
            if (!response.ok) throw new Error('Failed to fetch board data');

            const data = await response.json();
            lastBoardData = data;
            connectionStatus = 'connected';
            renderBoard(data, container);
        } catch (error) {
            console.error('TaskYou Board Error:', error);
            connectionStatus = 'error';

            // If we have cached data, show it with error status
            if (lastBoardData) {
                renderBoard(lastBoardData, container);
            } else {
                renderError(container);
            }
        }
    }

    /**
     * Render the board with columns and tasks
     */
    function renderBoard(data, container) {
        const columns = data.columns || [];

        // Reorder columns
        const order = ['backlog', 'queued', 'processing', 'blocked', 'done'];
        const sortedColumns = [...columns].sort((a, b) =>
            order.indexOf(a.status) - order.indexOf(b.status)
        );

        // Filter to show relevant columns (always show processing, hide empty done)
        const visibleColumns = sortedColumns.filter(col => {
            if (col.status === 'processing') return true;
            if (col.status === 'done') return col.tasks && col.tasks.length > 0;
            return col.tasks && col.tasks.length > 0;
        });

        const statusDotClass = connectionStatus === 'connected' ? 'connected' :
                               connectionStatus === 'connecting' ? 'connecting' : 'error';
        const statusText = connectionStatus === 'connected' ? 'Live' :
                          connectionStatus === 'connecting' ? 'Connecting...' : 'Reconnecting...';

        let html = `
            <div class="taskyou-board-container">
                <div class="taskyou-header">
                    <div class="taskyou-title">
                        <span>\u{1F4CB}</span>
                        <span>Live Task Board</span>
                    </div>
                    <div class="taskyou-status">
                        <span class="taskyou-status-dot ${statusDotClass}"></span>
                        <span>${statusText}</span>
                        <span id="taskyou-last-update"></span>
                    </div>
                </div>
                <div class="taskyou-columns">
        `;

        for (const column of visibleColumns) {
            html += renderColumn(column);
        }

        html += `
                </div>
            </div>
        `;
        container.innerHTML = html;

        // Update timestamp
        updateLastRefresh(data.updated_at);

        // Attach click handlers
        attachTaskClickHandlers();
    }

    /**
     * Render a single column
     */
    function renderColumn(column) {
        const config = COLUMN_CONFIG[column.status] || COLUMN_CONFIG.backlog;
        const tasks = column.tasks || [];
        const displayTasks = tasks.slice(0, MAX_TASKS_PER_COLUMN);
        const hiddenCount = tasks.length - displayTasks.length;

        let html = `
            <div class="taskyou-column" data-status="${column.status}">
                <div class="taskyou-column-header">
                    <span class="taskyou-column-icon" style="color: ${config.color}">${config.icon}</span>
                    <span class="taskyou-column-title">${config.label}</span>
                    <span class="taskyou-column-count">${column.count}</span>
                </div>
                <div class="taskyou-tasks">
        `;

        if (displayTasks.length === 0) {
            html += '<div class="taskyou-empty">No tasks</div>';
        } else {
            for (const task of displayTasks) {
                html += renderTask(task, column.status);
            }

            if (hiddenCount > 0) {
                html += `<div class="taskyou-more">+${hiddenCount} more</div>`;
            }
        }

        html += `
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Render a single task card
     */
    function renderTask(task, status) {
        const typeIcon = TYPE_ICONS[task.type] || TYPE_ICONS.default;
        const statusClass = status === 'done' ? 'completed' : (status === 'processing' ? 'active' : '');

        return `
            <div class="taskyou-task ${statusClass}" data-task-id="${task.id}" title="Click to view output">
                <div class="taskyou-task-header">
                    <span class="taskyou-task-icon">${typeIcon}</span>
                    <div class="taskyou-task-content">
                        <span class="taskyou-task-title">${escapeHtml(task.title)}</span>
                        <span class="taskyou-task-age">${task.age_hint}</span>
                    </div>
                    <span class="taskyou-task-id">#${task.id}</span>
                </div>
            </div>
        `;
    }

    /**
     * Attach click handlers to task cards
     */
    function attachTaskClickHandlers() {
        const tasks = document.querySelectorAll('.taskyou-task[data-task-id]');
        tasks.forEach(task => {
            task.addEventListener('click', () => {
                const taskId = parseInt(task.dataset.taskId, 10);
                openOutputModal(taskId);
            });
        });
    }

    /**
     * Open the output modal for a task
     */
    async function openOutputModal(taskId) {
        selectedTaskId = taskId;
        isOutputModalOpen = true;

        // Find task info from last board data
        let taskInfo = null;
        if (lastBoardData && lastBoardData.columns) {
            for (const col of lastBoardData.columns) {
                if (col.tasks) {
                    taskInfo = col.tasks.find(t => t.id === taskId);
                    if (taskInfo) break;
                }
            }
        }

        const taskTitle = taskInfo ? taskInfo.title : `Task #${taskId}`;

        // Create modal
        const overlay = document.createElement('div');
        overlay.className = 'taskyou-modal-overlay';
        overlay.id = 'taskyou-output-modal';
        overlay.innerHTML = `
            <div class="taskyou-modal">
                <div class="taskyou-modal-header">
                    <div class="taskyou-modal-title">
                        <span>\u{1F4BB}</span>
                        <span>${escapeHtml(taskTitle)}</span>
                        <span style="opacity: 0.5">#${taskId}</span>
                    </div>
                    <button class="taskyou-modal-close" title="Close">&times;</button>
                </div>
                <div class="taskyou-modal-body">
                    <div class="taskyou-output" id="taskyou-output-content">
                        <div class="taskyou-loading-spinner" style="margin: 2rem auto;"></div>
                    </div>
                </div>
                <div class="taskyou-modal-footer">
                    <div class="taskyou-live-indicator">
                        <span class="taskyou-live-dot"></span>
                        <span>Auto-refreshing every 1.5s</span>
                    </div>
                    <span>Last ${OUTPUT_LINES} lines</span>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Close handlers
        overlay.querySelector('.taskyou-modal-close').addEventListener('click', closeOutputModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeOutputModal();
        });

        // Escape key handler
        const escHandler = (e) => {
            if (e.key === 'Escape') closeOutputModal();
        };
        document.addEventListener('keydown', escHandler);
        overlay._escHandler = escHandler;

        // Load output
        loadTaskOutput(taskId);
        startOutputRefresh(taskId);
    }

    /**
     * Close the output modal
     */
    function closeOutputModal() {
        const overlay = document.getElementById('taskyou-output-modal');
        if (overlay) {
            document.removeEventListener('keydown', overlay._escHandler);
            overlay.remove();
        }

        isOutputModalOpen = false;
        selectedTaskId = null;
        stopOutputRefresh();
    }

    /**
     * Load task output
     */
    async function loadTaskOutput(taskId) {
        const outputEl = document.getElementById('taskyou-output-content');
        if (!outputEl) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/task/${taskId}/output?lines=${OUTPUT_LINES}`);
            if (!response.ok) throw new Error('Failed to fetch output');

            const data = await response.json();
            const output = data.output ? data.output.trim() : '';

            if (output) {
                outputEl.textContent = output;
                // Auto-scroll to bottom
                outputEl.scrollTop = outputEl.scrollHeight;
            } else {
                outputEl.innerHTML = '<div class="taskyou-output-empty">No output available for this task</div>';
            }
        } catch (error) {
            console.error('Failed to load task output:', error);
            outputEl.innerHTML = '<div class="taskyou-output-empty">Failed to load output</div>';
        }
    }

    /**
     * Start auto-refresh for output
     */
    function startOutputRefresh(taskId) {
        stopOutputRefresh();
        outputRefreshTimer = setInterval(() => {
            if (isOutputModalOpen && selectedTaskId === taskId) {
                loadTaskOutput(taskId);
            }
        }, OUTPUT_REFRESH_INTERVAL);
    }

    /**
     * Stop output auto-refresh
     */
    function stopOutputRefresh() {
        if (outputRefreshTimer) {
            clearInterval(outputRefreshTimer);
            outputRefreshTimer = null;
        }
    }

    /**
     * Render error state
     */
    function renderError(container) {
        container.innerHTML = `
            <div class="taskyou-board-container">
                <div class="taskyou-error">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">\u{1F4CB}</div>
                    <span>Unable to connect to TaskYou server</span>
                    <br>
                    <button class="taskyou-retry" onclick="window.TaskYouBoard.refresh()">Retry Connection</button>
                </div>
            </div>
        `;
    }

    /**
     * Update the last refresh timestamp display
     */
    function updateLastRefresh(timestamp) {
        const element = document.getElementById('taskyou-last-update');
        if (!element) return;

        if (timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diffSec = Math.floor((now - date) / 1000);

            if (diffSec < 5) {
                element.textContent = 'just now';
            } else if (diffSec < 60) {
                element.textContent = `${diffSec}s ago`;
            } else {
                const diffMin = Math.floor(diffSec / 60);
                element.textContent = `${diffMin}m ago`;
            }
        }
    }

    /**
     * Start auto-refresh timer
     */
    function startAutoRefresh() {
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(loadBoard, REFRESH_INTERVAL);
    }

    /**
     * Stop auto-refresh timer
     */
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }

    /**
     * Handle visibility changes (pause when tab is hidden)
     */
    function handleVisibilityChange() {
        if (document.hidden) {
            stopAutoRefresh();
            stopOutputRefresh();
        } else {
            loadBoard();
            startAutoRefresh();
            if (isOutputModalOpen && selectedTaskId) {
                loadTaskOutput(selectedTaskId);
                startOutputRefresh(selectedTaskId);
            }
        }
    }

    /**
     * Manual refresh
     */
    function refresh() {
        connectionStatus = 'connecting';
        loadBoard();
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTaskYouBoard);
    } else {
        initTaskYouBoard();
    }

    // Expose public API
    window.TaskYouBoard = {
        refresh: refresh,
        stop: stopAutoRefresh,
        start: startAutoRefresh,
        setApiUrl: function(url) { API_BASE_URL = url; },
        getStatus: function() { return connectionStatus; }
    };
})();
