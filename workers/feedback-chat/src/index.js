/**
 * Feedback Chat Worker
 * Endpoints:
 *   POST /chat - AI-powered chat using Workers AI
 *   POST /feedback - Store feedback in KV
 *   GET /feedback - List all feedback (admin)
 *   GET /feedback/:id - Get specific feedback
 */

const SYSTEM_PROMPT = `You are a friendly assistant for "Rex Marks The Spot", a website about an AI-generated animated movie called "Fairy Dinosaur Date Night".

The movie features:
- Gabe & Nina (parents who get a date night)
- Mia & Leo (kid protagonists who go on an adventure)
- Ruben (a fairy godfather)
- Jetplane (a color-farting dinosaur)

Help visitors understand the project, answer questions about the movie and production process, and collect their feedback. Be enthusiastic but concise. If they want to leave feedback, encourage them to use the feedback form.`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers
    const corsHeaders = getCorsHeaders(request, env);

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route handling
      if (path === '/chat' && request.method === 'POST') {
        return handleChat(request, env, corsHeaders);
      }

      if (path === '/feedback' && request.method === 'POST') {
        return handleFeedbackSubmit(request, env, corsHeaders);
      }

      if (path === '/feedback' && request.method === 'GET') {
        return handleFeedbackList(request, env, corsHeaders);
      }

      if (path.startsWith('/feedback/') && request.method === 'GET') {
        const id = path.split('/feedback/')[1];
        return handleFeedbackGet(id, env, corsHeaders);
      }

      if (path.startsWith('/feedback/') && request.method === 'DELETE') {
        const id = path.split('/feedback/')[1];
        return handleFeedbackDelete(id, env, corsHeaders);
      }

      // Health check
      if (path === '/health') {
        return jsonResponse({ status: 'ok', service: 'feedback-chat' }, corsHeaders);
      }

      return jsonResponse({ error: 'Not found' }, corsHeaders, 404);

    } catch (error) {
      console.error('Worker error:', error);
      return jsonResponse({ error: 'Internal server error' }, corsHeaders, 500);
    }
  }
};

/**
 * Handle chat requests using Workers AI
 */
async function handleChat(request, env, corsHeaders) {
  const body = await request.json();
  const { message, history = [] } = body;

  if (!message || typeof message !== 'string') {
    return jsonResponse({ error: 'Message is required' }, corsHeaders, 400);
  }

  // Build messages array for the AI
  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    ...history.slice(-10), // Keep last 10 messages for context
    { role: 'user', content: message }
  ];

  try {
    // Use Workers AI with a text generation model
    const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
      messages: messages,
      max_tokens: 500,
      temperature: 0.7
    });

    return jsonResponse({
      response: response.response,
      model: 'llama-3.1-8b-instruct'
    }, corsHeaders);

  } catch (error) {
    console.error('AI error:', error);
    return jsonResponse({
      error: 'Failed to get AI response',
      details: error.message
    }, corsHeaders, 500);
  }
}

/**
 * Handle feedback submission
 */
async function handleFeedbackSubmit(request, env, corsHeaders) {
  const body = await request.json();
  const { name, email, type, message, page, chatHistory } = body;

  if (!message || typeof message !== 'string') {
    return jsonResponse({ error: 'Message is required' }, corsHeaders, 400);
  }

  // Generate unique ID
  const id = `fb_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const feedback = {
    id,
    name: name || 'Anonymous',
    email: email || null,
    type: type || 'general', // general, bug, suggestion, praise
    message,
    page: page || null,
    chatHistory: chatHistory || [],
    createdAt: new Date().toISOString(),
    status: 'new', // new, reviewed, resolved
    ip: request.headers.get('CF-Connecting-IP') || 'unknown',
    userAgent: request.headers.get('User-Agent') || 'unknown'
  };

  // Store in KV
  await env.FEEDBACK_KV.put(id, JSON.stringify(feedback));

  // Also maintain an index of all feedback IDs
  const indexKey = 'feedback_index';
  const existingIndex = await env.FEEDBACK_KV.get(indexKey);
  const index = existingIndex ? JSON.parse(existingIndex) : [];
  index.unshift(id); // Add to beginning (newest first)
  await env.FEEDBACK_KV.put(indexKey, JSON.stringify(index.slice(0, 1000))); // Keep last 1000

  return jsonResponse({
    success: true,
    id,
    message: 'Thank you for your feedback!'
  }, corsHeaders, 201);
}

/**
 * List all feedback (admin endpoint)
 */
async function handleFeedbackList(request, env, corsHeaders) {
  const url = new URL(request.url);
  const limit = parseInt(url.searchParams.get('limit') || '50');
  const offset = parseInt(url.searchParams.get('offset') || '0');
  const status = url.searchParams.get('status'); // Filter by status

  // Get index
  const indexKey = 'feedback_index';
  const existingIndex = await env.FEEDBACK_KV.get(indexKey);
  const index = existingIndex ? JSON.parse(existingIndex) : [];

  // Fetch feedback items
  const feedbackItems = [];
  const idsToFetch = index.slice(offset, offset + limit);

  for (const id of idsToFetch) {
    const data = await env.FEEDBACK_KV.get(id);
    if (data) {
      const item = JSON.parse(data);
      if (!status || item.status === status) {
        feedbackItems.push(item);
      }
    }
  }

  return jsonResponse({
    items: feedbackItems,
    total: index.length,
    limit,
    offset
  }, corsHeaders);
}

/**
 * Get specific feedback by ID
 */
async function handleFeedbackGet(id, env, corsHeaders) {
  const data = await env.FEEDBACK_KV.get(id);

  if (!data) {
    return jsonResponse({ error: 'Feedback not found' }, corsHeaders, 404);
  }

  return jsonResponse(JSON.parse(data), corsHeaders);
}

/**
 * Delete feedback by ID (admin)
 */
async function handleFeedbackDelete(id, env, corsHeaders) {
  // Remove from KV
  await env.FEEDBACK_KV.delete(id);

  // Remove from index
  const indexKey = 'feedback_index';
  const existingIndex = await env.FEEDBACK_KV.get(indexKey);
  if (existingIndex) {
    const index = JSON.parse(existingIndex).filter(i => i !== id);
    await env.FEEDBACK_KV.put(indexKey, JSON.stringify(index));
  }

  return jsonResponse({ success: true, deleted: id }, corsHeaders);
}

/**
 * Build CORS headers
 */
function getCorsHeaders(request, env) {
  const origin = request.headers.get('Origin') || '';
  const allowedOrigins = (env.ALLOWED_ORIGINS || '').split(',');

  // Allow localhost for development
  const isAllowed = allowedOrigins.some(o => origin.startsWith(o.trim())) ||
                    origin.includes('localhost') ||
                    origin.includes('127.0.0.1');

  return {
    'Access-Control-Allow-Origin': isAllowed ? origin : allowedOrigins[0],
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400'
  };
}

/**
 * JSON response helper
 */
function jsonResponse(data, corsHeaders, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders
    }
  });
}
