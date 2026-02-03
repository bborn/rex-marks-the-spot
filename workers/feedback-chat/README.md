# Feedback Chat Worker

LLM-powered feedback chat for Rex Marks The Spot using Cloudflare Workers AI and KV.

## Features

- **AI Chat**: Uses Llama 3.1 8B via Workers AI (free tier)
- **Feedback Storage**: Stores feedback in Cloudflare KV
- **Admin Panel**: View and manage feedback at `/feedback-admin.html`

## Setup

### 1. Install Wrangler CLI

```bash
npm install -g wrangler
wrangler login
```

### 2. Create KV Namespace

```bash
cd workers/feedback-chat
wrangler kv:namespace create FEEDBACK_KV
```

This outputs an ID like:
```
{ binding = "FEEDBACK_KV", id = "abcd1234..." }
```

### 3. Update wrangler.toml

Replace `YOUR_KV_NAMESPACE_ID` with the ID from step 2:

```toml
[[kv_namespaces]]
binding = "FEEDBACK_KV"
id = "abcd1234..."  # Your actual ID
```

### 4. Deploy

```bash
npm install
wrangler deploy
```

This outputs your worker URL:
```
https://feedback-chat.YOUR_SUBDOMAIN.workers.dev
```

### 5. Update Chat Widget

Edit `docs/js/chat-widget.js` and update the API URL:

```javascript
const CONFIG = {
  apiUrl: 'https://feedback-chat.YOUR_SUBDOMAIN.workers.dev',
};
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Send message to AI, get response |
| POST | `/feedback` | Submit feedback |
| GET | `/feedback` | List all feedback (admin) |
| GET | `/feedback/:id` | Get specific feedback |
| DELETE | `/feedback/:id` | Delete feedback |
| GET | `/health` | Health check |

## Chat Request

```json
POST /chat
{
  "message": "What is this movie about?",
  "history": [
    { "role": "user", "content": "Hi" },
    { "role": "assistant", "content": "Hello!" }
  ]
}
```

## Feedback Request

```json
POST /feedback
{
  "name": "Visitor Name",
  "email": "email@example.com",
  "type": "suggestion",
  "message": "Great project!",
  "page": "/behind-the-scenes.html",
  "chatHistory": []
}
```

## Local Development

```bash
wrangler dev
```

Opens local server at `http://localhost:8787`

## Costs

- **Workers AI**: Free tier includes generous allowance for Llama 3.1 8B
- **KV Storage**: Free tier includes 100,000 reads/day, 1,000 writes/day
- **Workers**: Free tier includes 100,000 requests/day

For a low-traffic website, this should be completely free.
