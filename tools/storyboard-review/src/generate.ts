import { Env } from './api';

const R2_PUBLIC_URL = 'https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev';

interface StartFrameInput {
  panel_id: string;
  scene_description: string;
  hero_shot_url?: string;
  character_refs?: string[];
}

interface ClipInput {
  panel_id: string;
  start_frame_url: string;
  motion_prompt: string;
  duration_seconds?: number;
}

interface FullPanelInput {
  panel_id: string;
  scene_description: string;
  motion_prompt: string;
  hero_shot_url?: string;
  character_refs?: string[];
}

// ─── Gemini: generate a start frame ─────────────────────────────────────────

async function generateStartFrame(input: StartFrameInput, env: Env): Promise<{ start_url: string; r2_path: string }> {
  const apiKey = env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('GEMINI_API_KEY not configured');

  // Build parts: text prompt + reference images
  const parts: any[] = [];

  // Add reference images inline if provided
  const refUrls = [
    ...(input.hero_shot_url ? [input.hero_shot_url] : []),
    ...(input.character_refs || []),
  ];

  for (const url of refUrls) {
    try {
      const imgResp = await fetch(url);
      if (imgResp.ok) {
        const buf = await imgResp.arrayBuffer();
        const base64 = arrayBufferToBase64(buf);
        const mime = imgResp.headers.get('content-type') || 'image/png';
        parts.push({
          inline_data: { mime_type: mime, data: base64 },
        });
      }
    } catch {
      // Skip failed reference image fetches
    }
  }

  // Text prompt
  parts.push({
    text: `Generate a storyboard panel image based on this description. Match the style of the reference images if provided. Use a 16:9 aspect ratio, cinematic composition, Pixar-style animation look.\n\nScene description: ${input.scene_description}`,
  });

  const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=${apiKey}`;

  const resp = await fetch(geminiUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts }],
      generationConfig: {
        responseModalities: ['TEXT', 'IMAGE'],
      },
    }),
  });

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Gemini API error (${resp.status}): ${errText}`);
  }

  const data: any = await resp.json();

  // Extract generated image from response
  const candidates = data.candidates || [];
  if (!candidates.length) throw new Error('Gemini returned no candidates');

  const responseParts = candidates[0].content?.parts || [];
  const imagePart = responseParts.find((p: any) => p.inline_data?.mime_type?.startsWith('image/'));
  if (!imagePart) throw new Error('Gemini returned no image in response');

  const imageData = base64ToArrayBuffer(imagePart.inline_data.data);
  const mimeType = imagePart.inline_data.mime_type;
  const ext = mimeType === 'image/jpeg' ? 'jpg' : 'png';

  // Upload to R2
  const r2Path = `storyboards/v3/scene-01/${input.panel_id}-start.${ext}`;
  await env.ASSETS.put(r2Path, imageData, {
    httpMetadata: { contentType: mimeType },
  });

  return {
    start_url: `${R2_PUBLIC_URL}/${r2Path}`,
    r2_path: r2Path,
  };
}

// ─── Replicate P-Video: generate a video clip ───────────────────────────────

async function generateClip(input: ClipInput, env: Env): Promise<{ video_url: string; end_url: string }> {
  const apiToken = env.REPLICATE_API_TOKEN;
  if (!apiToken) throw new Error('REPLICATE_API_TOKEN not configured');

  // Download start frame
  const startFrameResp = await fetch(input.start_frame_url);
  if (!startFrameResp.ok) throw new Error(`Failed to download start frame: ${startFrameResp.status}`);
  const startFrameBuffer = await startFrameResp.arrayBuffer();
  const startFrameBase64 = arrayBufferToBase64(startFrameBuffer);
  const startFrameMime = startFrameResp.headers.get('content-type') || 'image/png';
  const startFrameDataUri = `data:${startFrameMime};base64,${startFrameBase64}`;

  // Create prediction on Replicate
  const createResp = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'prunaai/p-video',
      input: {
        image: startFrameDataUri,
        prompt: input.motion_prompt,
        num_frames: Math.min((input.duration_seconds || 3) * 8, 48),
      },
    }),
  });

  if (!createResp.ok) {
    const errText = await createResp.text();
    throw new Error(`Replicate create error (${createResp.status}): ${errText}`);
  }

  const prediction: any = await createResp.json();
  let predictionId = prediction.id;

  // Poll for completion (max 5 minutes)
  const maxWait = 300_000;
  const pollInterval = 5_000;
  let elapsed = 0;
  let result: any = prediction;

  while (result.status !== 'succeeded' && result.status !== 'failed' && result.status !== 'canceled') {
    if (elapsed >= maxWait) throw new Error('P-Video generation timed out');
    await sleep(pollInterval);
    elapsed += pollInterval;

    const pollResp = await fetch(`https://api.replicate.com/v1/predictions/${predictionId}`, {
      headers: { 'Authorization': `Bearer ${apiToken}` },
    });
    if (!pollResp.ok) throw new Error(`Replicate poll error: ${pollResp.status}`);
    result = await pollResp.json();
  }

  if (result.status === 'failed') throw new Error(`P-Video failed: ${result.error || 'unknown error'}`);
  if (result.status === 'canceled') throw new Error('P-Video generation was canceled');

  // Get video output URL
  const videoOutputUrl = Array.isArray(result.output) ? result.output[0] : result.output;
  if (!videoOutputUrl) throw new Error('P-Video returned no output');

  // Download video
  const videoResp = await fetch(videoOutputUrl);
  if (!videoResp.ok) throw new Error(`Failed to download video: ${videoResp.status}`);
  const videoBuffer = await videoResp.arrayBuffer();

  // Upload video to R2
  const videoR2Path = `storyboards/v3/scene-01/${input.panel_id}-clip.mp4`;
  await env.ASSETS.put(videoR2Path, videoBuffer, {
    httpMetadata: { contentType: 'video/mp4' },
  });
  const videoR2Url = `${R2_PUBLIC_URL}/${videoR2Path}`;

  // Extract last frame using a simple approach:
  // We can't run ffmpeg in Workers, so we'll use the start frame as a fallback end frame
  // and let the user regenerate if needed. In practice, we generate end frame from the video
  // by re-using the Gemini API to describe/capture the last frame.
  // For now: upload the start frame as end frame placeholder, mark it for later extraction.
  const endR2Path = `storyboards/v3/scene-01/${input.panel_id}-end.png`;

  // Try to extract last frame via a lightweight approach:
  // Use Gemini to generate an end frame description based on the motion
  // Actually, simplest: just set end_url to empty and let user extract manually
  // OR: we can ask Gemini to generate what the end frame looks like

  // For MVP: copy start frame as end frame placeholder
  const startFrameForEnd = await fetch(input.start_frame_url);
  if (startFrameForEnd.ok) {
    const endBuffer = await startFrameForEnd.arrayBuffer();
    await env.ASSETS.put(endR2Path, endBuffer, {
      httpMetadata: { contentType: 'image/png' },
    });
  }

  return {
    video_url: videoR2Url,
    end_url: `${R2_PUBLIC_URL}/${endR2Path}`,
  };
}

// ─── Full panel: start frame + clip in sequence ─────────────────────────────

async function generateFullPanel(input: FullPanelInput, env: Env): Promise<{ start_url: string; end_url: string; video_url: string }> {
  // Step 1: Generate start frame
  const startResult = await generateStartFrame({
    panel_id: input.panel_id,
    scene_description: input.scene_description,
    hero_shot_url: input.hero_shot_url,
    character_refs: input.character_refs,
  }, env);

  // Step 2: Generate clip from start frame
  const clipResult = await generateClip({
    panel_id: input.panel_id,
    start_frame_url: startResult.start_url,
    motion_prompt: input.motion_prompt,
  }, env);

  return {
    start_url: startResult.start_url,
    end_url: clipResult.end_url,
    video_url: clipResult.video_url,
  };
}

// ─── Route handler ──────────────────────────────────────────────────────────

export async function handleGenerate(request: Request, env: Env, path: string): Promise<Response> {
  if (request.method !== 'POST') {
    return json({ error: 'Method not allowed' }, 405);
  }

  try {
    const body: any = await request.json();

    // POST /api/generate/start-frame
    if (path === '/api/generate/start-frame') {
      if (!body.panel_id || !body.scene_description) {
        return json({ error: 'panel_id and scene_description required' }, 400);
      }
      const result = await generateStartFrame(body, env);

      // Update panel in DB
      await env.DB.prepare(
        'UPDATE panels SET start_url = ? WHERE id = ?'
      ).bind(result.start_url, body.panel_id).run();

      return json(result);
    }

    // POST /api/generate/clip
    if (path === '/api/generate/clip') {
      if (!body.panel_id || !body.start_frame_url || !body.motion_prompt) {
        return json({ error: 'panel_id, start_frame_url, and motion_prompt required' }, 400);
      }
      const result = await generateClip(body, env);

      // Update panel in DB
      await env.DB.prepare(
        'UPDATE panels SET video_url = ?, end_url = ? WHERE id = ?'
      ).bind(result.video_url, result.end_url, body.panel_id).run();

      return json(result);
    }

    // POST /api/generate/full-panel
    if (path === '/api/generate/full-panel') {
      if (!body.panel_id || !body.scene_description || !body.motion_prompt) {
        return json({ error: 'panel_id, scene_description, and motion_prompt required' }, 400);
      }
      const result = await generateFullPanel(body, env);

      // Update panel in DB
      await env.DB.prepare(
        'UPDATE panels SET start_url = ?, end_url = ?, video_url = ? WHERE id = ?'
      ).bind(result.start_url, result.end_url, result.video_url, body.panel_id).run();

      return json(result);
    }

    return json({ error: 'Unknown generate endpoint' }, 404);
  } catch (err: any) {
    console.error('Generation error:', err);
    return json({ error: err.message || 'Generation failed' }, 500);
  }
}

export function handleStatus(env: Env): Response {
  return json({
    status: 'ok',
    gemini_configured: !!env.GEMINI_API_KEY,
    replicate_configured: !!env.REPLICATE_API_TOKEN,
    r2_configured: !!env.ASSETS,
  });
}

// ─── Utilities ──────────────────────────────────────────────────────────────

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
