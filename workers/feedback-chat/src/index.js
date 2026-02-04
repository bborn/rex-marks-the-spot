/**
 * Feedback Chat Worker
 * Endpoints:
 *   POST /chat - AI-powered chat using Workers AI
 *   POST /feedback - Store feedback in KV
 *   GET /feedback - List all feedback (admin)
 *   GET /feedback/:id - Get specific feedback
 *
 * Panel Feedback Endpoints:
 *   POST /panel-feedback - Submit feedback for a storyboard panel
 *   GET /panel-feedback/:panelId - Get feedback for a specific panel
 *   GET /panel-feedback/counts - Get feedback counts by panel
 *   PUT /panel-feedback/:id/status - Update feedback status (director only)
 *   DELETE /panel-feedback/:id - Delete panel feedback (director only)
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

      // Panel feedback endpoints
      if (path === '/panel-feedback' && request.method === 'POST') {
        return handlePanelFeedbackSubmit(request, env, corsHeaders);
      }

      if (path === '/panel-feedback/counts' && request.method === 'GET') {
        return handlePanelFeedbackCounts(request, env, corsHeaders);
      }

      if (path.match(/^\/panel-feedback\/[^/]+\/status$/) && request.method === 'PUT') {
        const id = path.split('/panel-feedback/')[1].replace('/status', '');
        return handlePanelFeedbackStatusUpdate(id, request, env, corsHeaders);
      }

      if (path.match(/^\/panel-feedback\/panel\//)) {
        const panelId = path.split('/panel-feedback/panel/')[1];
        if (request.method === 'GET') {
          return handlePanelFeedbackGet(panelId, env, corsHeaders);
        }
      }

      if (path.match(/^\/panel-feedback\/[^/]+$/) && request.method === 'DELETE') {
        const id = path.split('/panel-feedback/')[1];
        return handlePanelFeedbackDelete(id, request, env, corsHeaders);
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

// ============================================
// Panel Feedback Functions
// ============================================

/**
 * Validate director authentication
 * Uses a simple token-based auth via Authorization header
 */
function isDirectorAuthenticated(request, env) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader) return false;

  const token = authHeader.replace('Bearer ', '');
  return token === env.DIRECTOR_TOKEN;
}

/**
 * Generate a panel ID key from act, scene, panel
 * Format: act1-scene01-panel02
 */
function getPanelKey(act, scene, panel) {
  const sceneNum = String(scene).padStart(2, '0');
  const panelNum = String(panel).padStart(2, '0');
  return `act${act}-scene${sceneNum}-panel${panelNum}`;
}

/**
 * Rate limiting for public comments
 * Returns true if rate limited
 */
async function isRateLimited(ip, env) {
  const rateLimitKey = `rate_limit_${ip}`;
  const existing = await env.FEEDBACK_KV.get(rateLimitKey);

  if (existing) {
    const data = JSON.parse(existing);
    const timeSinceFirst = Date.now() - data.firstRequest;
    const oneHour = 60 * 60 * 1000;

    if (timeSinceFirst < oneHour) {
      if (data.count >= 10) {
        return true; // Rate limited: max 10 comments per hour
      }
      data.count++;
      await env.FEEDBACK_KV.put(rateLimitKey, JSON.stringify(data), { expirationTtl: 3600 });
      return false;
    }
  }

  // Start new rate limit window
  await env.FEEDBACK_KV.put(rateLimitKey, JSON.stringify({
    firstRequest: Date.now(),
    count: 1
  }), { expirationTtl: 3600 });

  return false;
}

/**
 * Handle panel feedback submission
 */
async function handlePanelFeedbackSubmit(request, env, corsHeaders) {
  const body = await request.json();
  const { act, scene, panel, message, name } = body;

  // Validate required fields
  if (!act || !scene || !panel || !message) {
    return jsonResponse({ error: 'act, scene, panel, and message are required' }, corsHeaders, 400);
  }

  if (typeof message !== 'string' || message.length < 1 || message.length > 2000) {
    return jsonResponse({ error: 'Message must be 1-2000 characters' }, corsHeaders, 400);
  }

  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const isDirector = isDirectorAuthenticated(request, env);

  // Rate limit public comments
  if (!isDirector) {
    const limited = await isRateLimited(ip, env);
    if (limited) {
      return jsonResponse({ error: 'Rate limited. Please wait before submitting more comments.' }, corsHeaders, 429);
    }
  }

  const panelKey = getPanelKey(act, scene, panel);
  const id = `pf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const feedback = {
    id,
    panelKey,
    act: parseInt(act),
    scene: parseInt(scene),
    panel: parseInt(panel),
    message: message.trim(),
    name: isDirector ? 'Director' : (name || 'Anonymous').slice(0, 50),
    isDirector,
    status: 'new', // new, noted, addressed
    createdAt: new Date().toISOString(),
    ip: isDirector ? null : ip,
    userAgent: request.headers.get('User-Agent') || 'unknown'
  };

  // Store feedback
  await env.FEEDBACK_KV.put(id, JSON.stringify(feedback));

  // Update panel index (list of feedback IDs per panel)
  const panelIndexKey = `panel_index_${panelKey}`;
  const existingIndex = await env.FEEDBACK_KV.get(panelIndexKey);
  const index = existingIndex ? JSON.parse(existingIndex) : [];
  index.unshift(id);
  await env.FEEDBACK_KV.put(panelIndexKey, JSON.stringify(index.slice(0, 100))); // Keep last 100 per panel

  // Update global panel feedback index
  const globalIndexKey = 'panel_feedback_index';
  const globalIndex = await env.FEEDBACK_KV.get(globalIndexKey);
  const gIndex = globalIndex ? JSON.parse(globalIndex) : [];
  gIndex.unshift(id);
  await env.FEEDBACK_KV.put(globalIndexKey, JSON.stringify(gIndex.slice(0, 5000)));

  // Update counts cache
  const countsKey = 'panel_feedback_counts';
  const countsData = await env.FEEDBACK_KV.get(countsKey);
  const counts = countsData ? JSON.parse(countsData) : {};
  counts[panelKey] = (counts[panelKey] || 0) + 1;
  await env.FEEDBACK_KV.put(countsKey, JSON.stringify(counts));

  return jsonResponse({
    success: true,
    id,
    panelKey,
    isDirector,
    message: isDirector ? 'Director feedback submitted!' : 'Thank you for your feedback!'
  }, corsHeaders, 201);
}

/**
 * Get feedback for a specific panel
 */
async function handlePanelFeedbackGet(panelId, env, corsHeaders) {
  const panelIndexKey = `panel_index_${panelId}`;
  const existingIndex = await env.FEEDBACK_KV.get(panelIndexKey);

  if (!existingIndex) {
    return jsonResponse({ items: [], panelId }, corsHeaders);
  }

  const index = JSON.parse(existingIndex);
  const items = [];

  for (const id of index) {
    const data = await env.FEEDBACK_KV.get(id);
    if (data) {
      const item = JSON.parse(data);
      // Remove sensitive data for public view
      delete item.ip;
      delete item.userAgent;
      items.push(item);
    }
  }

  // Sort: director comments first, then by date
  items.sort((a, b) => {
    if (a.isDirector && !b.isDirector) return -1;
    if (!a.isDirector && b.isDirector) return 1;
    return new Date(b.createdAt) - new Date(a.createdAt);
  });

  return jsonResponse({ items, panelId }, corsHeaders);
}

/**
 * Get feedback counts for all panels
 */
async function handlePanelFeedbackCounts(request, env, corsHeaders) {
  const countsKey = 'panel_feedback_counts';
  const countsData = await env.FEEDBACK_KV.get(countsKey);
  const counts = countsData ? JSON.parse(countsData) : {};

  return jsonResponse({ counts }, corsHeaders);
}

/**
 * Update feedback status (director only)
 */
async function handlePanelFeedbackStatusUpdate(id, request, env, corsHeaders) {
  if (!isDirectorAuthenticated(request, env)) {
    return jsonResponse({ error: 'Unauthorized' }, corsHeaders, 401);
  }

  const body = await request.json();
  const { status } = body;

  if (!['new', 'noted', 'addressed'].includes(status)) {
    return jsonResponse({ error: 'Invalid status. Use: new, noted, addressed' }, corsHeaders, 400);
  }

  const data = await env.FEEDBACK_KV.get(id);
  if (!data) {
    return jsonResponse({ error: 'Feedback not found' }, corsHeaders, 404);
  }

  const feedback = JSON.parse(data);
  feedback.status = status;
  feedback.updatedAt = new Date().toISOString();

  await env.FEEDBACK_KV.put(id, JSON.stringify(feedback));

  return jsonResponse({ success: true, id, status }, corsHeaders);
}

/**
 * Delete panel feedback (director only)
 */
async function handlePanelFeedbackDelete(id, request, env, corsHeaders) {
  if (!isDirectorAuthenticated(request, env)) {
    return jsonResponse({ error: 'Unauthorized' }, corsHeaders, 401);
  }

  const data = await env.FEEDBACK_KV.get(id);
  if (!data) {
    return jsonResponse({ error: 'Feedback not found' }, corsHeaders, 404);
  }

  const feedback = JSON.parse(data);
  const panelKey = feedback.panelKey;

  // Remove from KV
  await env.FEEDBACK_KV.delete(id);

  // Remove from panel index
  const panelIndexKey = `panel_index_${panelKey}`;
  const existingIndex = await env.FEEDBACK_KV.get(panelIndexKey);
  if (existingIndex) {
    const index = JSON.parse(existingIndex).filter(i => i !== id);
    await env.FEEDBACK_KV.put(panelIndexKey, JSON.stringify(index));
  }

  // Remove from global index
  const globalIndexKey = 'panel_feedback_index';
  const globalIndex = await env.FEEDBACK_KV.get(globalIndexKey);
  if (globalIndex) {
    const gIndex = JSON.parse(globalIndex).filter(i => i !== id);
    await env.FEEDBACK_KV.put(globalIndexKey, JSON.stringify(gIndex));
  }

  // Update counts
  const countsKey = 'panel_feedback_counts';
  const countsData = await env.FEEDBACK_KV.get(countsKey);
  if (countsData) {
    const counts = JSON.parse(countsData);
    if (counts[panelKey] > 0) {
      counts[panelKey]--;
      if (counts[panelKey] === 0) delete counts[panelKey];
      await env.FEEDBACK_KV.put(countsKey, JSON.stringify(counts));
    }
  }

  return jsonResponse({ success: true, deleted: id }, corsHeaders);
}

/**
 * Build CORS headers
 */
function getCorsHeaders(request, env) {
  const origin = request.headers.get('Origin') || '';
  const allowedOrigins = (env.ALLOWED_ORIGINS || '').split(',').map(o => o.trim());

  // Allow localhost for development
  const isAllowed = allowedOrigins.includes(origin) ||
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
