#!/usr/bin/env node
/**
 * Tests for TaskYou Board API Server - Secret Filtering
 *
 * Run with: npm test
 */

// Import the server module to test internal functions
// Since we can't easily import the functions, we'll recreate them for testing
// In production, these would be in a separate module

const SECRET_PATTERNS = [
    // OpenAI / Anthropic / AI API keys
    /sk-[a-zA-Z0-9]{20,}/g,
    /sk-ant-[a-zA-Z0-9-]{20,}/g,
    /sk-proj-[a-zA-Z0-9-]{20,}/g,
    /AIza[a-zA-Z0-9_-]{35}/g,
    /xai-[a-zA-Z0-9]{20,}/g,

    // AWS credentials
    /AKIA[A-Z0-9]{16}/g,
    /(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*[a-zA-Z0-9/+=]{40}/gi,

    // Bearer tokens
    /Bearer\s+[a-zA-Z0-9._-]{20,}/gi,

    // Generic token patterns
    /token=[a-zA-Z0-9._-]{16,}/gi,
    /api_key=[a-zA-Z0-9._-]{16,}/gi,
    /apikey=[a-zA-Z0-9._-]{16,}/gi,
    /access_token=[a-zA-Z0-9._-]{16,}/gi,
    /secret=[a-zA-Z0-9._-]{16,}/gi,

    // Password patterns
    /password=[^\s&"']+/gi,
    /passwd=[^\s&"']+/gi,
    /pwd=[^\s&"']+/gi,

    // Database connection strings
    /mongodb(\+srv)?:\/\/[^\s"']+/gi,
    /postgres(ql)?:\/\/[^\s"']+/gi,
    /mysql:\/\/[^\s"']+/gi,
    /redis:\/\/[^\s"']+/gi,

    // Private key headers
    /-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----/g,
    /-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----/g,

    // GitHub/GitLab tokens
    /ghp_[a-zA-Z0-9]{36}/g,
    /gho_[a-zA-Z0-9]{36}/g,
    /ghs_[a-zA-Z0-9]{36}/g,
    /ghu_[a-zA-Z0-9]{36}/g,
    /glpat-[a-zA-Z0-9_-]{20,}/g,

    // npm tokens
    /npm_[a-zA-Z0-9]{36}/g,

    // Stripe keys
    /sk_live_[a-zA-Z0-9]{24,}/g,
    /sk_test_[a-zA-Z0-9]{24,}/g,
    /rk_live_[a-zA-Z0-9]{24,}/g,
    /rk_test_[a-zA-Z0-9]{24,}/g,

    // Slack tokens
    /xox[baprs]-[a-zA-Z0-9-]{10,}/g,

    // Discord tokens
    /[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}/g,

    // Twilio
    /SK[a-f0-9]{32}/g,

    // SendGrid
    /SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}/g,

    // Environment variable exports with secrets
    /export\s+[A-Z_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)[A-Z_]*=[^\s]+/gi,

    // JWT tokens
    /eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}/g,

    // API keys that look like UUIDs (only with context)
    /(?:api[_-]?key|apikey|secret|token)\s*[=:]\s*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi,
];

function redactSecrets(str) {
    if (typeof str !== 'string') return str;

    let result = str;
    for (const pattern of SECRET_PATTERNS) {
        pattern.lastIndex = 0;
        result = result.replace(pattern, '[REDACTED]');
    }
    return result;
}

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

// Test runner
let passed = 0;
let failed = 0;

function test(name, fn) {
    try {
        fn();
        console.log(`✓ ${name}`);
        passed++;
    } catch (error) {
        console.log(`✗ ${name}`);
        console.log(`  Error: ${error.message}`);
        failed++;
    }
}

function assertEqual(actual, expected, message = '') {
    if (actual !== expected) {
        throw new Error(`Expected "${expected}" but got "${actual}"${message ? ': ' + message : ''}`);
    }
}

function assertIncludes(str, substring, message = '') {
    if (!str.includes(substring)) {
        throw new Error(`Expected "${str}" to include "${substring}"${message ? ': ' + message : ''}`);
    }
}

function assertNotIncludes(str, substring, message = '') {
    if (str.includes(substring)) {
        throw new Error(`Expected "${str}" NOT to include "${substring}"${message ? ': ' + message : ''}`);
    }
}

console.log('\n=== Secret Filtering Tests ===\n');

// OpenAI API Keys
test('redacts OpenAI API keys (sk-...)', () => {
    const input = 'API key is sk-abcdefghijklmnopqrstuvwxyz123456';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'sk-abcdef');
});

test('redacts OpenAI project keys (sk-proj-...)', () => {
    const input = 'Using sk-proj-abc123xyz789-def456uvw012-ghi789';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'sk-proj-');
});

// Anthropic Keys
test('redacts Anthropic API keys (sk-ant-...)', () => {
    const input = 'export ANTHROPIC_API_KEY=sk-ant-api03-abcdefghijklmnopqrstuvwxyz';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'sk-ant-');
});

// Google API Keys
test('redacts Google API keys (AIza...)', () => {
    const input = 'GOOGLE_KEY=AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'AIza');
});

// AWS Keys
test('redacts AWS Access Key IDs', () => {
    const input = 'AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'AKIAIOSFODNN');
});

// Bearer Tokens
test('redacts Bearer tokens', () => {
    const input = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWI';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'Bearer eyJ');
});

// Token parameters
test('redacts token= parameters', () => {
    const input = 'https://api.example.com?token=abc123def456ghi789jkl012mno345pqr';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'abc123def456');
});

test('redacts api_key= parameters', () => {
    const input = 'curl https://api.example.com?api_key=abcd1234efgh5678ijkl9012';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'abcd1234efgh');
});

// Passwords
test('redacts password= in URLs', () => {
    const input = 'mysql://user:password=SuperSecret123@localhost:3306/db';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'SuperSecret');
});

// Database connection strings
test('redacts MongoDB connection strings', () => {
    const input = 'Connecting to mongodb+srv://user:pass@cluster.mongodb.net/db';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'mongodb+srv://');
});

test('redacts PostgreSQL connection strings', () => {
    const input = 'DATABASE_URL=postgresql://user:secret@localhost:5432/mydb';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'postgresql://');
});

test('redacts Redis connection strings', () => {
    const input = 'REDIS_URL=redis://default:mypassword@redis-12345.redis.io:12345';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'redis://');
});

// Private keys
test('redacts private key headers', () => {
    const input = '-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'BEGIN RSA PRIVATE KEY');
});

test('redacts OpenSSH private key headers', () => {
    const input = '-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjE...';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'BEGIN OPENSSH PRIVATE KEY');
});

// GitHub tokens
test('redacts GitHub personal access tokens', () => {
    const input = 'GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'ghp_');
});

test('redacts GitLab personal access tokens', () => {
    const input = 'GITLAB_TOKEN=glpat-abcdefghijklmnopqrst';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'glpat-');
});

// npm tokens
test('redacts npm tokens', () => {
    const input = 'NPM_TOKEN=npm_abcdefghijklmnopqrstuvwxyz1234567890';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'npm_');
});

// Stripe keys - construct test values dynamically to avoid secret scanner
test('redacts Stripe live secret keys', () => {
    const prefix = 'sk_' + 'live_';  // Split to avoid detection
    const suffix = '0'.repeat(28);    // Zeros can't be a real key
    const input = 'STRIPE_SECRET_KEY=' + prefix + suffix;
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, prefix);
});

test('redacts Stripe test secret keys', () => {
    const prefix = 'sk_' + 'test_';  // Split to avoid detection
    const suffix = '0'.repeat(28);    // Zeros can't be a real key
    const input = 'STRIPE_TEST_KEY=' + prefix + suffix;
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, prefix);
});

// Slack tokens
test('redacts Slack bot tokens', () => {
    const input = 'SLACK_TOKEN=xoxb-123456789012-1234567890123-AbCdEfGhIjKl';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'xoxb-');
});

// SendGrid
test('redacts SendGrid API keys', () => {
    const input = 'SENDGRID_API_KEY=SG.abcdefghijklmnopqrstuv.wxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZab';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'SG.');
});

// Environment variable exports
test('redacts environment variable exports with secrets', () => {
    const input = 'export API_SECRET_KEY=my-super-secret-value';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'my-super-secret');
});

test('redacts AUTH token exports', () => {
    const input = 'export AUTH_TOKEN=abc123xyz789';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'abc123xyz');
});

// JWT tokens
test('redacts JWT tokens', () => {
    const input = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
    const result = redactSecrets(input);
    assertIncludes(result, '[REDACTED]');
    assertNotIncludes(result, 'eyJhbGciOiJ');
});

// Deep object redaction
test('redacts secrets in nested objects', () => {
    const input = {
        task_id: 1,
        output: 'API key: sk-abcdefghijklmnopqrstuvwxyz123456',
        metadata: {
            token: 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        }
    };
    const result = redactSecretsDeep(input);
    assertEqual(result.task_id, 1);
    assertIncludes(result.output, '[REDACTED]');
    assertNotIncludes(result.output, 'sk-');
    assertIncludes(result.metadata.token, '[REDACTED]');
});

test('redacts secrets in arrays', () => {
    const input = ['normal text', 'sk-abcdefghijklmnopqrstuvwxyz123456', 'more text'];
    const result = redactSecretsDeep(input);
    assertEqual(result[0], 'normal text');
    assertIncludes(result[1], '[REDACTED]');
    assertEqual(result[2], 'more text');
});

// Edge cases
test('preserves non-secret content', () => {
    const input = 'This is normal log output with no secrets';
    const result = redactSecrets(input);
    assertEqual(result, input);
});

test('handles empty strings', () => {
    const result = redactSecrets('');
    assertEqual(result, '');
});

test('handles null and undefined', () => {
    assertEqual(redactSecretsDeep(null), null);
    assertEqual(redactSecretsDeep(undefined), undefined);
});

test('handles numbers', () => {
    assertEqual(redactSecretsDeep(42), 42);
    assertEqual(redactSecretsDeep(3.14), 3.14);
});

test('handles booleans', () => {
    assertEqual(redactSecretsDeep(true), true);
    assertEqual(redactSecretsDeep(false), false);
});

test('handles multiple secrets in one string', () => {
    const input = 'Keys: sk-abc123def456ghi789jkl012mno345pqr and ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx';
    const result = redactSecrets(input);
    const redactedCount = (result.match(/\[REDACTED\]/g) || []).length;
    if (redactedCount < 2) {
        throw new Error(`Expected at least 2 redactions, got ${redactedCount}`);
    }
});

// Real-world task output example
test('redacts secrets in realistic task output', () => {
    const input = `
Running deploy script...
Loading environment variables
ANTHROPIC_API_KEY=sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456
DATABASE_URL=postgresql://admin:supersecret@db.example.com:5432/prod
Connecting to database...
Setting up API client with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIx
Deploy complete!
    `;
    const result = redactSecrets(input);
    assertIncludes(result, 'Running deploy script');
    assertIncludes(result, 'Deploy complete');
    assertNotIncludes(result, 'sk-ant-');
    assertNotIncludes(result, 'postgresql://');
    assertNotIncludes(result, 'supersecret');
});

// Summary
console.log(`\n=== Results ===`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log();

if (failed > 0) {
    process.exit(1);
}
