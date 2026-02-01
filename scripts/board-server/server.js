#!/usr/bin/env node
/**
 * TaskYou Board API Server
 *
 * Provides real-time access to TaskYou board data via REST API.
 * Designed to be polled every 2-3 seconds for live updates.
 *
 * Endpoints:
 *   GET /api/board          - Returns current board state (ty board --json)
 *   GET /api/task/:id/output - Returns recent output for a task (ty output :id --lines N)
 *   GET /health             - Health check endpoint
 */

const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

const app = express();
const PORT = process.env.PORT || 3080;
const TY_PATH = process.env.TY_PATH || '/home/rex/.local/bin/ty';

// CORS configuration - allow rexmarksthespot.com and localhost for development
const corsOptions = {
    origin: [
        'https://rexmarksthespot.com',
        'https://www.rexmarksthespot.com',
        'http://rexmarksthespot.com',
        'http://www.rexmarksthespot.com',
        /^http:\/\/localhost(:\d+)?$/,
        /^http:\/\/127\.0\.0\.1(:\d+)?$/
    ],
    methods: ['GET'],
    optionsSuccessStatus: 200
};

app.use(cors(corsOptions));
app.use(express.json());

/**
 * Secret filtering patterns - these will be redacted from all API responses
 * SECURITY: Add new patterns here as needed
 */
const SECRET_PATTERNS = [
    // OpenAI / Anthropic / AI API keys
    /sk-[a-zA-Z0-9]{20,}/g,                          // OpenAI keys (sk-...)
    /sk-ant-[a-zA-Z0-9-]{20,}/g,                     // Anthropic keys
    /sk-proj-[a-zA-Z0-9-]{20,}/g,                    // OpenAI project keys
    /AIza[a-zA-Z0-9_-]{35}/g,                        // Google API keys
    /xai-[a-zA-Z0-9]{20,}/g,                         // xAI/Grok keys

    // AWS credentials
    /AKIA[A-Z0-9]{16}/g,                             // AWS Access Key ID
    /(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*[a-zA-Z0-9/+=]{40}/gi,  // AWS Secret with context

    // Bearer tokens
    /Bearer\s+[a-zA-Z0-9._-]{20,}/gi,                // Bearer tokens

    // Generic token patterns in URLs/params
    /token=[a-zA-Z0-9._-]{16,}/gi,                   // token= parameters
    /api_key=[a-zA-Z0-9._-]{16,}/gi,                 // api_key= parameters
    /apikey=[a-zA-Z0-9._-]{16,}/gi,                  // apikey= parameters
    /access_token=[a-zA-Z0-9._-]{16,}/gi,            // access_token= parameters
    /secret=[a-zA-Z0-9._-]{16,}/gi,                  // secret= parameters

    // Password patterns
    /password=[^\s&"']+/gi,                          // password= in URLs/strings
    /passwd=[^\s&"']+/gi,                            // passwd= in URLs/strings
    /pwd=[^\s&"']+/gi,                               // pwd= in URLs/strings

    // Database connection strings
    /mongodb(\+srv)?:\/\/[^\s"']+/gi,                // MongoDB URLs
    /postgres(ql)?:\/\/[^\s"']+/gi,                  // PostgreSQL URLs
    /mysql:\/\/[^\s"']+/gi,                          // MySQL URLs
    /redis:\/\/[^\s"']+/gi,                          // Redis URLs

    // SSH/RSA private keys (partial match for log lines)
    /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/g,     // Private key headers
    /-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----/g,   // OpenSSH key headers

    // GitHub/GitLab tokens
    /ghp_[a-zA-Z0-9]{36}/g,                          // GitHub personal access tokens
    /gho_[a-zA-Z0-9]{36}/g,                          // GitHub OAuth tokens
    /ghs_[a-zA-Z0-9]{36}/g,                          // GitHub server-to-server tokens
    /ghu_[a-zA-Z0-9]{36}/g,                          // GitHub user-to-server tokens
    /glpat-[a-zA-Z0-9_-]{20,}/g,                     // GitLab personal access tokens

    // npm tokens
    /npm_[a-zA-Z0-9]{36}/g,                          // npm tokens

    // Stripe keys
    /sk_live_[a-zA-Z0-9]{24,}/g,                     // Stripe live secret
    /sk_test_[a-zA-Z0-9]{24,}/g,                     // Stripe test secret
    /rk_live_[a-zA-Z0-9]{24,}/g,                     // Stripe restricted key
    /rk_test_[a-zA-Z0-9]{24,}/g,                     // Stripe restricted test

    // Slack tokens
    /xox[baprs]-[a-zA-Z0-9-]{10,}/g,                 // Slack tokens

    // Discord tokens
    /[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}/g,    // Discord bot tokens

    // Twilio
    /SK[a-f0-9]{32}/g,                               // Twilio API keys

    // SendGrid
    /SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}/g,    // SendGrid API keys

    // Environment variable exports with secrets
    /export\s+[A-Z_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)[A-Z_]*=[^\s]+/gi,

    // JWT tokens (simplified - captures most JWTs)
    /eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}/g,

    // Heroku API key / API keys that look like UUIDs (only with context)
    /(?:api[_-]?key|apikey|secret|token)\s*[=:]\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi,
];

/**
 * Redact secrets from a string
 */
function redactSecrets(str) {
    if (typeof str !== 'string') return str;

    let result = str;
    for (const pattern of SECRET_PATTERNS) {
        // Reset lastIndex for global patterns
        pattern.lastIndex = 0;
        result = result.replace(pattern, '[REDACTED]');
    }
    return result;
}

/**
 * Recursively redact secrets from any value (object, array, string)
 */
function redactSecretsDeep(value) {
    if (typeof value === 'string') {
        return redactSecrets(value);
    }

    if (Array.isArray(value)) {
        return value.map(item => redactSecretsDeep(item));
    }

    if (value !== null && typeof value === 'object') {
        const result = {};
        for (const key of Object.keys(value)) {
            result[key] = redactSecretsDeep(value[key]);
        }
        return result;
    }

    return value;
}

/**
 * Middleware to filter secrets from all JSON responses
 * SECURITY: This wraps res.json() to sanitize all outgoing data
 */
app.use((req, res, next) => {
    const originalJson = res.json.bind(res);

    res.json = function(data) {
        const sanitizedData = redactSecretsDeep(data);
        return originalJson(sanitizedData);
    };

    next();
});

// Cache for board data (to prevent excessive ty calls)
let boardCache = {
    data: null,
    timestamp: 0,
    ttl: 1000 // 1 second TTL
};

/**
 * Execute ty command and return output
 */
async function runTyCommand(args, options = {}) {
    const timeout = options.timeout || 10000;

    try {
        const { stdout, stderr } = await execAsync(`${TY_PATH} ${args}`, {
            timeout,
            maxBuffer: 1024 * 1024, // 1MB buffer
            env: { ...process.env, HOME: '/home/rex' }
        });
        return { success: true, stdout, stderr };
    } catch (error) {
        console.error(`ty command failed: ${args}`, error.message);
        return { success: false, error: error.message };
    }
}

/**
 * GET /api/board
 * Returns the current board state from ty board --json
 */
app.get('/api/board', async (req, res) => {
    const now = Date.now();

    // Return cached data if still valid
    if (boardCache.data && (now - boardCache.timestamp) < boardCache.ttl) {
        return res.json(boardCache.data);
    }

    const result = await runTyCommand('board --json');

    if (!result.success) {
        return res.status(500).json({
            error: 'Failed to fetch board data',
            message: result.error
        });
    }

    try {
        const boardData = JSON.parse(result.stdout);

        // Add server metadata
        const response = {
            ...boardData,
            updated_at: new Date().toISOString(),
            server_version: '1.0.0'
        };

        // Update cache
        boardCache = {
            data: response,
            timestamp: now,
            ttl: 1000
        };

        res.json(response);
    } catch (parseError) {
        console.error('Failed to parse board JSON:', parseError);
        res.status(500).json({
            error: 'Failed to parse board data',
            message: parseError.message
        });
    }
});

/**
 * GET /api/task/:id/output
 * Returns recent output for a specific task
 * Query params:
 *   - lines: number of lines to return (default: 20, max: 100)
 */
app.get('/api/task/:id/output', async (req, res) => {
    const taskId = parseInt(req.params.id, 10);

    if (isNaN(taskId) || taskId < 1) {
        return res.status(400).json({
            error: 'Invalid task ID',
            message: 'Task ID must be a positive integer'
        });
    }

    const lines = Math.min(Math.max(parseInt(req.query.lines, 10) || 20, 1), 100);

    const result = await runTyCommand(`output ${taskId} --lines ${lines}`);

    if (!result.success) {
        return res.status(500).json({
            error: 'Failed to fetch task output',
            message: result.error,
            task_id: taskId
        });
    }

    res.json({
        task_id: taskId,
        lines: lines,
        output: result.stdout,
        updated_at: new Date().toISOString()
    });
});

/**
 * GET /api/task/:id
 * Returns detailed info for a specific task
 */
app.get('/api/task/:id', async (req, res) => {
    const taskId = parseInt(req.params.id, 10);

    if (isNaN(taskId) || taskId < 1) {
        return res.status(400).json({
            error: 'Invalid task ID',
            message: 'Task ID must be a positive integer'
        });
    }

    const result = await runTyCommand(`show ${taskId} --json`);

    if (!result.success) {
        return res.status(500).json({
            error: 'Failed to fetch task details',
            message: result.error,
            task_id: taskId
        });
    }

    try {
        const taskData = JSON.parse(result.stdout);
        res.json({
            ...taskData,
            updated_at: new Date().toISOString()
        });
    } catch (parseError) {
        // If JSON parsing fails, the task might not exist
        res.status(404).json({
            error: 'Task not found or invalid response',
            message: parseError.message,
            task_id: taskId
        });
    }
});

/**
 * GET /health
 * Health check endpoint for monitoring
 */
app.get('/health', async (req, res) => {
    const tyCheck = await runTyCommand('--version', { timeout: 5000 });

    res.json({
        status: tyCheck.success ? 'healthy' : 'degraded',
        timestamp: new Date().toISOString(),
        ty_available: tyCheck.success,
        uptime: process.uptime()
    });
});

/**
 * 404 handler
 */
app.use((req, res) => {
    res.status(404).json({
        error: 'Not found',
        message: `Endpoint ${req.method} ${req.path} does not exist`,
        available_endpoints: [
            'GET /api/board',
            'GET /api/task/:id',
            'GET /api/task/:id/output',
            'GET /health'
        ]
    });
});

/**
 * Error handler
 */
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err.message
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`TaskYou Board API Server running on port ${PORT}`);
    console.log(`Endpoints:`);
    console.log(`  GET http://localhost:${PORT}/api/board`);
    console.log(`  GET http://localhost:${PORT}/api/task/:id`);
    console.log(`  GET http://localhost:${PORT}/api/task/:id/output`);
    console.log(`  GET http://localhost:${PORT}/health`);
    console.log(`\nCORS enabled for: rexmarksthespot.com, localhost`);
});
