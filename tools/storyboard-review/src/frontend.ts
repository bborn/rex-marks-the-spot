export function renderHome(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Storyboard Review</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #111; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; }
  h1 { margin-bottom: 24px; font-size: 24px; }
  .scene-list { display: flex; flex-direction: column; gap: 12px; max-width: 600px; }
  .scene-link { display: block; padding: 16px 20px; background: #1a1a1a; border: 1px solid #282828; border-radius: 8px; color: #e0e0e0; text-decoration: none; font-size: 16px; transition: border-color 0.2s; }
  .scene-link:hover { border-color: #555; }
  .loading { color: #888; }
</style>
</head>
<body>
<h1>Storyboard Review</h1>
<div class="scene-list" id="scenes"><span class="loading">Loading scenes...</span></div>
<script>
fetch('/api/scenes').then(r=>r.json()).then(scenes => {
  const el = document.getElementById('scenes');
  if (!scenes.length) { el.innerHTML = '<p class="loading">No scenes yet. Seed one via POST /api/scenes/:id/seed</p>'; return; }
  el.innerHTML = scenes.map(s => '<a class="scene-link" href="/'+s.id+'">'+s.name+'</a>').join('');
});
</script>
</body>
</html>`;
}

export function renderPage(sceneId: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Storyboard Review — ${sceneId}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #111; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

/* Top bar */
.topbar { display: flex; align-items: center; gap: 16px; padding: 12px 20px; background: #1a1a1a; border-bottom: 1px solid #282828; position: sticky; top: 0; z-index: 100; }
.topbar h1 { font-size: 16px; font-weight: 600; }
.topbar .back { color: #888; text-decoration: none; font-size: 14px; }
.topbar .back:hover { color: #e0e0e0; }

/* Stats bar */
.stats { display: flex; gap: 16px; padding: 8px 20px; background: #161616; border-bottom: 1px solid #282828; font-size: 13px; }
.stat { display: flex; align-items: center; gap: 4px; }
.stat .dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.pending { background: #666; }
.dot.approved { background: #4caf50; }
.dot.needs_fix { background: #ff9800; }
.dot.redo { background: #f44336; }

/* Mode selector */
.modes { display: flex; gap: 4px; margin-left: auto; }
.mode-btn { padding: 4px 12px; border: 1px solid #333; background: transparent; color: #888; border-radius: 4px; cursor: pointer; font-size: 12px; }
.mode-btn.active { background: #333; color: #e0e0e0; border-color: #555; }
.export-btn { padding: 4px 12px; border: 1px solid #333; background: transparent; color: #4caf50; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px; }
.export-btn:hover { background: #1a3a1a; }

/* Panel grid */
.panels { padding: 20px; display: flex; flex-direction: column; gap: 24px; }
.panel-card { background: #1a1a1a; border: 2px solid #282828; border-radius: 8px; overflow: hidden; transition: border-color 0.2s; }
.panel-card.approved { border-color: #4caf50; }
.panel-card.needs_fix { border-color: #ff9800; }
.panel-card.redo { border-color: #f44336; }

.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid #282828; }
.panel-header h3 { font-size: 14px; font-weight: 500; }
.panel-actions { display: flex; gap: 4px; }
.status-btn { padding: 3px 10px; border: 1px solid #333; background: transparent; border-radius: 4px; cursor: pointer; font-size: 11px; color: #888; }
.status-btn:hover { border-color: #555; }
.status-btn.active-approved { background: #1b3a1b; color: #4caf50; border-color: #4caf50; }
.status-btn.active-needs_fix { background: #3a2a0a; color: #ff9800; border-color: #ff9800; }
.status-btn.active-redo { background: #3a1010; color: #f44336; border-color: #f44336; }

/* Frames */
.frames { display: grid; grid-template-columns: 1fr 1fr; }
.frames.has-video { grid-template-columns: 1fr 1fr 1fr; }
.frame { position: relative; }
.frame-label { position: absolute; top: 6px; left: 8px; background: rgba(0,0,0,0.7); color: #aaa; font-size: 10px; padding: 2px 6px; border-radius: 3px; z-index: 10; pointer-events: none; }
.frame img { width: 100%; display: block; user-select: none; -webkit-user-drag: none; }

/* Video clip */
.video-frame { position: relative; background: #000; display: flex; align-items: center; justify-content: center; }
.video-frame video { width: 100%; display: block; }
.video-frame .frame-label { pointer-events: none; }

/* Annotations overlay */
.annotation-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.pin { position: absolute; width: 22px; height: 22px; background: #f44336; border: 2px solid #fff; border-radius: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #fff; cursor: pointer; z-index: 20; }
.pin:hover { transform: translate(-50%, -50%) scale(1.2); }
.rect { position: absolute; border: 2px dashed #ff9800; background: rgba(255,152,0,0.1); cursor: pointer; z-index: 20; }
.rect .rect-num { position: absolute; top: -10px; left: -10px; width: 18px; height: 18px; background: #ff9800; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; color: #000; }

/* Annotation list */
.annotation-list { padding: 8px 14px; border-top: 1px solid #282828; }
.annotation-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; }
.annotation-item .num { width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #fff; flex-shrink: 0; }
.annotation-item .num.pin-num { background: #f44336; }
.annotation-item .num.rect-num { background: #ff9800; color: #000; }
.annotation-item input { flex: 1; background: #111; border: 1px solid #333; color: #e0e0e0; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.annotation-item input:focus { outline: none; border-color: #555; }
.annotation-item .frame-tag { font-size: 10px; color: #666; width: 36px; flex-shrink: 0; }
.annotation-item .delete-btn { background: transparent; border: none; color: #666; cursor: pointer; font-size: 14px; padding: 2px 4px; }
.annotation-item .delete-btn:hover { color: #f44336; }

/* Drawing overlay for rectangles */
.draw-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 15; }
.draw-rect { position: absolute; border: 2px dashed #ff9800; background: rgba(255,152,0,0.15); }

.saving { position: fixed; bottom: 16px; right: 16px; background: #333; color: #aaa; padding: 6px 14px; border-radius: 4px; font-size: 12px; opacity: 0; transition: opacity 0.3s; z-index: 200; }
.saving.show { opacity: 1; }
</style>
</head>
<body>
<div class="topbar">
  <a href="/" class="back">&larr; Scenes</a>
  <h1 id="scene-title">${sceneId}</h1>
  <div class="modes">
    <button class="mode-btn active" data-mode="pin">Pin</button>
    <button class="mode-btn" data-mode="region">Region</button>
    <button class="mode-btn" data-mode="view">View</button>
  </div>
  <button class="export-btn" id="export-btn">Export JSON</button>
</div>
<div class="stats" id="stats"></div>
<div class="panels" id="panels"></div>
<div class="saving" id="saving">Saving...</div>

<script>
const SCENE_ID = '${sceneId}';
let panels = [];
let currentMode = 'pin';
let drawState = null;

// Mode selector
document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;
    updateCursors();
  });
});

function updateCursors() {
  document.querySelectorAll('.frame').forEach(f => {
    if (currentMode === 'pin') f.style.cursor = 'crosshair';
    else if (currentMode === 'region') f.style.cursor = 'crosshair';
    else f.style.cursor = 'default';
  });
}

// Saving indicator
function showSaving() {
  const el = document.getElementById('saving');
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 800);
}

async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: {} };
  if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  const res = await fetch(path, opts);
  return res.json();
}

// Load panels
async function loadPanels() {
  panels = await api('/api/scenes/' + SCENE_ID + '/panels');
  render();
}

function updateStats() {
  const counts = { pending: 0, approved: 0, needs_fix: 0, redo: 0 };
  panels.forEach(p => counts[p.status] = (counts[p.status] || 0) + 1);
  document.getElementById('stats').innerHTML =
    '<span class="stat"><span class="dot pending"></span> Pending: ' + counts.pending + '</span>' +
    '<span class="stat"><span class="dot approved"></span> Approved: ' + counts.approved + '</span>' +
    '<span class="stat"><span class="dot needs_fix"></span> Needs Fix: ' + counts.needs_fix + '</span>' +
    '<span class="stat"><span class="dot redo"></span> Redo: ' + counts.redo + '</span>' +
    '<span class="stat" style="margin-left:auto">Total: ' + panels.length + '</span>';
}

function render() {
  updateStats();
  const container = document.getElementById('panels');
  container.innerHTML = panels.map((panel, pi) => {
    const annotations = panel.annotations || [];
    return '<div class="panel-card ' + panel.status + '" data-panel-idx="' + pi + '">' +
      '<div class="panel-header">' +
        '<h3>' + panel.panel_number + ' — ' + escHtml(panel.name) + '</h3>' +
        '<div class="panel-actions">' +
          statusBtn(panel, 'approved', 'Approved') +
          statusBtn(panel, 'needs_fix', 'Needs Fix') +
          statusBtn(panel, 'redo', 'Redo') +
        '</div>' +
      '</div>' +
      '<div class="frames' + (panel.video_url ? ' has-video' : '') + '">' +
        renderFrame(panel, 'start', annotations) +
        (panel.video_url ? renderVideoClip(panel.video_url) : '') +
        renderFrame(panel, 'end', annotations) +
      '</div>' +
      renderAnnotationList(panel, annotations) +
    '</div>';
  }).join('');
  bindEvents();
  updateCursors();
}

function statusBtn(panel, status, label) {
  const active = panel.status === status ? ' active-' + status : '';
  return '<button class="status-btn' + active + '" data-panel-id="' + panel.id + '" data-status="' + status + '">' + label + '</button>';
}

function renderFrame(panel, frame, annotations) {
  const url = frame === 'start' ? panel.start_url : panel.end_url;
  const frameAnnotations = annotations.filter(a => a.frame === frame);
  let overlayHtml = '';
  frameAnnotations.forEach((a, i) => {
    const globalIdx = annotations.indexOf(a) + 1;
    if (a.type === 'pin') {
      overlayHtml += '<div class="pin" style="left:' + (a.x * 100) + '%;top:' + (a.y * 100) + '%">' + globalIdx + '</div>';
    } else if (a.type === 'region') {
      overlayHtml += '<div class="rect" style="left:' + (a.x * 100) + '%;top:' + (a.y * 100) + '%;width:' + ((a.w || 0) * 100) + '%;height:' + ((a.h || 0) * 100) + '%"><span class="rect-num">' + globalIdx + '</span></div>';
    }
  });
  return '<div class="frame" data-panel-id="' + panel.id + '" data-frame="' + frame + '">' +
    '<span class="frame-label">' + frame + '</span>' +
    '<img src="' + url + '" loading="lazy" draggable="false">' +
    '<div class="annotation-layer">' + overlayHtml + '</div>' +
  '</div>';
}

function renderVideoClip(videoUrl) {
  return '<div class="video-frame">' +
    '<span class="frame-label">clip</span>' +
    '<video src="' + videoUrl + '" controls preload="metadata" loop></video>' +
  '</div>';
}

function renderAnnotationList(panel, annotations) {
  if (!annotations.length) return '';
  return '<div class="annotation-list">' +
    annotations.map((a, i) => {
      const numClass = a.type === 'pin' ? 'pin-num' : 'rect-num';
      return '<div class="annotation-item">' +
        '<span class="num ' + numClass + '">' + (i + 1) + '</span>' +
        '<span class="frame-tag">' + a.frame + '</span>' +
        '<input type="text" value="' + escAttr(a.text || '') + '" data-annotation-id="' + a.id + '" placeholder="Add note...">' +
        '<button class="delete-btn" data-annotation-id="' + a.id + '" data-panel-id="' + panel.id + '">&times;</button>' +
      '</div>';
    }).join('') +
  '</div>';
}

function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escAttr(s) { return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function bindEvents() {
  // Status buttons
  document.querySelectorAll('.status-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const panelId = btn.dataset.panelId;
      const status = btn.dataset.status;
      const panel = panels.find(p => p.id === panelId);
      // Toggle off if already active
      const newStatus = panel.status === status ? 'pending' : status;
      await api('/api/panels/' + panelId + '/status', 'PUT', { status: newStatus });
      panel.status = newStatus;
      showSaving();
      render();
    });
  });

  // Frame clicks (pin/region)
  document.querySelectorAll('.frame').forEach(frame => {
    frame.addEventListener('mousedown', (e) => {
      if (currentMode === 'view') return;
      if (e.target.closest('.pin') || e.target.closest('.rect')) return;
      const rect = frame.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;

      if (currentMode === 'pin') {
        addAnnotation(frame.dataset.panelId, frame.dataset.frame, 'pin', x, y);
      } else if (currentMode === 'region') {
        drawState = { panelId: frame.dataset.panelId, frameName: frame.dataset.frame, startX: x, startY: y, el: frame };
        // Create temporary draw rect
        const drawRect = document.createElement('div');
        drawRect.className = 'draw-rect';
        drawRect.style.left = (x * 100) + '%';
        drawRect.style.top = (y * 100) + '%';
        drawRect.style.width = '0';
        drawRect.style.height = '0';
        frame.querySelector('.annotation-layer').appendChild(drawRect);
        drawState.drawRect = drawRect;
      }
    });

    frame.addEventListener('mousemove', (e) => {
      if (!drawState || drawState.el !== frame) return;
      const rect = frame.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      const left = Math.min(drawState.startX, x);
      const top = Math.min(drawState.startY, y);
      const w = Math.abs(x - drawState.startX);
      const h = Math.abs(y - drawState.startY);
      drawState.drawRect.style.left = (left * 100) + '%';
      drawState.drawRect.style.top = (top * 100) + '%';
      drawState.drawRect.style.width = (w * 100) + '%';
      drawState.drawRect.style.height = (h * 100) + '%';
    });

    frame.addEventListener('mouseup', (e) => {
      if (!drawState || drawState.el !== frame) return;
      const rect = frame.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      const left = Math.min(drawState.startX, x);
      const top = Math.min(drawState.startY, y);
      const w = Math.abs(x - drawState.startX);
      const h = Math.abs(y - drawState.startY);
      drawState.drawRect.remove();
      if (w > 0.01 && h > 0.01) {
        addAnnotation(drawState.panelId, drawState.frameName, 'region', left, top, w, h);
      }
      drawState = null;
    });
  });

  // Cancel draw on mouseleave
  document.addEventListener('mouseup', () => {
    if (drawState) {
      if (drawState.drawRect) drawState.drawRect.remove();
      drawState = null;
    }
  });

  // Annotation text editing
  document.querySelectorAll('.annotation-item input').forEach(input => {
    let debounceTimer;
    input.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async () => {
        const annId = input.dataset.annotationId;
        await api('/api/annotations/' + annId, 'PUT', { text: input.value });
        // Update local state
        for (const p of panels) {
          const ann = (p.annotations || []).find(a => a.id == annId);
          if (ann) { ann.text = input.value; break; }
        }
        showSaving();
      }, 400);
    });
  });

  // Delete annotation
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const annId = btn.dataset.annotationId;
      const panelId = btn.dataset.panelId;
      await api('/api/annotations/' + annId, 'DELETE');
      const panel = panels.find(p => p.id === panelId);
      if (panel) panel.annotations = panel.annotations.filter(a => a.id != annId);
      showSaving();
      render();
    });
  });
}

async function addAnnotation(panelId, frame, type, x, y, w, h) {
  const result = await api('/api/panels/' + panelId + '/annotations', 'POST', { type, frame, x, y, w: w || null, h: h || null, text: '' });
  const panel = panels.find(p => p.id === panelId);
  if (panel) {
    panel.annotations = panel.annotations || [];
    panel.annotations.push({ id: result.id, type, frame, x, y, w, h, text: '' });
  }
  showSaving();
  render();
}

// Export
document.getElementById('export-btn').addEventListener('click', async () => {
  const data = await api('/api/scenes/' + SCENE_ID + '/feedback');
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = SCENE_ID + '-feedback.json';
  a.click();
});

// Scene title
api('/api/scenes').then(scenes => {
  const scene = scenes.find(s => s.id === SCENE_ID);
  if (scene) document.getElementById('scene-title').textContent = scene.name;
});

loadPanels();
</script>
</body>
</html>`;
}
