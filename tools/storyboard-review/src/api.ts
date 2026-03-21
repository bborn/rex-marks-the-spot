export interface Env {
  DB: D1Database;
  ASSETS: R2Bucket;
  GEMINI_API_KEY: string;
  REPLICATE_API_TOKEN: string;
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function handleApi(request: Request, env: Env, path: string): Promise<Response> {
  const url = new URL(request.url);
  const method = request.method;

  // GET /api/scenes
  if (method === 'GET' && path === '/api/scenes') {
    const { results } = await env.DB.prepare('SELECT * FROM scenes ORDER BY created_at').all();
    return json(results);
  }

  // GET /api/scenes/:id/panels
  const panelsMatch = path.match(/^\/api\/scenes\/([^/]+)\/panels$/);
  if (method === 'GET' && panelsMatch) {
    const sceneId = panelsMatch[1];
    const { results: panels } = await env.DB.prepare(
      'SELECT * FROM panels WHERE scene_id = ? ORDER BY panel_number'
    ).bind(sceneId).all();

    // Fetch annotations for each panel
    const panelIds = panels.map((p: any) => p.id);
    const panelsWithAnnotations = [];
    for (const panel of panels) {
      const { results: annotations } = await env.DB.prepare(
        'SELECT * FROM annotations WHERE panel_id = ? ORDER BY id'
      ).bind((panel as any).id).all();
      panelsWithAnnotations.push({ ...panel, annotations });
    }
    return json(panelsWithAnnotations);
  }

  // PUT /api/panels/:id/status
  const statusMatch = path.match(/^\/api\/panels\/([^/]+)\/status$/);
  if (method === 'PUT' && statusMatch) {
    const panelId = statusMatch[1];
    const body: any = await request.json();
    await env.DB.prepare('UPDATE panels SET status = ? WHERE id = ?')
      .bind(body.status, panelId).run();
    return json({ ok: true });
  }

  // POST /api/panels/:id/annotations
  const annotMatch = path.match(/^\/api\/panels\/([^/]+)\/annotations$/);
  if (method === 'POST' && annotMatch) {
    const panelId = annotMatch[1];
    const body: any = await request.json();
    const result = await env.DB.prepare(
      'INSERT INTO annotations (panel_id, type, frame, x, y, w, h, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    ).bind(panelId, body.type, body.frame, body.x, body.y, body.w || null, body.h || null, body.text || '').run();
    return json({ ok: true, id: result.meta.last_row_id });
  }

  // PUT /api/annotations/:id
  const updateAnnotMatch = path.match(/^\/api\/annotations\/(\d+)$/);
  if (method === 'PUT' && updateAnnotMatch) {
    const id = updateAnnotMatch[1];
    const body: any = await request.json();
    await env.DB.prepare('UPDATE annotations SET text = ? WHERE id = ?')
      .bind(body.text, id).run();
    return json({ ok: true });
  }

  // DELETE /api/annotations/:id
  const deleteAnnotMatch = path.match(/^\/api\/annotations\/(\d+)$/);
  if (method === 'DELETE' && deleteAnnotMatch) {
    const id = deleteAnnotMatch[1];
    await env.DB.prepare('DELETE FROM annotations WHERE id = ?').bind(id).run();
    return json({ ok: true });
  }

  // GET /api/scenes/:id/feedback
  const feedbackMatch = path.match(/^\/api\/scenes\/([^/]+)\/feedback$/);
  if (method === 'GET' && feedbackMatch) {
    const sceneId = feedbackMatch[1];
    const { results: scene } = await env.DB.prepare('SELECT * FROM scenes WHERE id = ?').bind(sceneId).all();
    if (!scene.length) return json({ error: 'Scene not found' }, 404);

    const { results: panels } = await env.DB.prepare(
      'SELECT * FROM panels WHERE scene_id = ? ORDER BY panel_number'
    ).bind(sceneId).all();

    const feedback: any = {
      scene: scene[0],
      exported_at: new Date().toISOString(),
      panels: [],
    };

    for (const panel of panels) {
      const { results: annotations } = await env.DB.prepare(
        'SELECT * FROM annotations WHERE panel_id = ? ORDER BY id'
      ).bind((panel as any).id).all();
      feedback.panels.push({
        ...panel,
        annotations,
      });
    }
    return json(feedback);
  }

  // PUT /api/scenes/:id/settings
  const settingsMatch = path.match(/^\/api\/scenes\/([^/]+)\/settings$/);
  if (method === 'PUT' && settingsMatch) {
    const sceneId = settingsMatch[1];
    const body: any = await request.json();
    const updates: string[] = [];
    const binds: any[] = [];
    if (body.hero_shot_url !== undefined) { updates.push('hero_shot_url = ?'); binds.push(body.hero_shot_url); }
    if (body.character_refs !== undefined) { updates.push('character_refs = ?'); binds.push(JSON.stringify(body.character_refs)); }
    if (!updates.length) return json({ error: 'No fields to update' }, 400);
    binds.push(sceneId);
    await env.DB.prepare(`UPDATE scenes SET ${updates.join(', ')} WHERE id = ?`).bind(...binds).run();
    return json({ ok: true });
  }

  // GET /api/scenes/:id/settings
  const getSettingsMatch = path.match(/^\/api\/scenes\/([^/]+)\/settings$/);
  if (method === 'GET' && getSettingsMatch) {
    const sceneId = getSettingsMatch[1];
    const { results } = await env.DB.prepare('SELECT hero_shot_url, character_refs FROM scenes WHERE id = ?').bind(sceneId).all();
    if (!results.length) return json({ error: 'Scene not found' }, 404);
    const scene: any = results[0];
    return json({
      hero_shot_url: scene.hero_shot_url || null,
      character_refs: scene.character_refs ? JSON.parse(scene.character_refs) : [],
    });
  }

  // PUT /api/panels/:id/metadata
  const metadataMatch = path.match(/^\/api\/panels\/([^/]+)\/metadata$/);
  if (method === 'PUT' && metadataMatch) {
    const panelId = metadataMatch[1];
    const body: any = await request.json();
    const updates: string[] = [];
    const binds: any[] = [];
    if (body.scene_description !== undefined) { updates.push('scene_description = ?'); binds.push(body.scene_description); }
    if (body.motion_prompt !== undefined) { updates.push('motion_prompt = ?'); binds.push(body.motion_prompt); }
    if (!updates.length) return json({ error: 'No fields to update' }, 400);
    binds.push(panelId);
    await env.DB.prepare(`UPDATE panels SET ${updates.join(', ')} WHERE id = ?`).bind(...binds).run();
    return json({ ok: true });
  }

  // POST /api/scenes/:id/seed
  const seedMatch = path.match(/^\/api\/scenes\/([^/]+)\/seed$/);
  if (method === 'POST' && seedMatch) {
    const sceneId = seedMatch[1];
    const body: any = await request.json();

    // Upsert scene
    await env.DB.prepare(
      'INSERT OR REPLACE INTO scenes (id, name) VALUES (?, ?)'
    ).bind(sceneId, body.name).run();

    // Insert panels
    const batch = body.panels.map((p: any) =>
      env.DB.prepare(
        'INSERT OR REPLACE INTO panels (id, scene_id, panel_number, name, start_url, end_url, status, video_url, scene_description, motion_prompt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
      ).bind(p.id, sceneId, p.panel_number, p.name, p.start_url, p.end_url, p.status || 'pending', p.video_url || null, p.scene_description || null, p.motion_prompt || null)
    );
    await env.DB.batch(batch);
    return json({ ok: true, panels_seeded: body.panels.length });
  }

  return json({ error: 'Not found' }, 404);
}
