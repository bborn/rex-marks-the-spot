import { handleApi, Env } from './api';
import { handleGenerate, handleStatus } from './generate';
import { renderPage, renderHome } from './frontend';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // API routes
    if (path.startsWith('/api/')) {
      // Handle CORS preflight
      if (request.method === 'OPTIONS') {
        return new Response(null, {
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
          },
        });
      }

      // Generation endpoints
      if (path.startsWith('/api/generate/')) {
        const response = await handleGenerate(request, env, path);
        response.headers.set('Access-Control-Allow-Origin', '*');
        return response;
      }

      // Status endpoint
      if (path === '/api/status') {
        const response = handleStatus(env);
        response.headers.set('Access-Control-Allow-Origin', '*');
        return response;
      }

      const response = await handleApi(request, env, path);
      response.headers.set('Access-Control-Allow-Origin', '*');
      return response;
    }

    // Home page — list scenes
    if (path === '/' || path === '') {
      return new Response(renderHome(), {
        headers: { 'Content-Type': 'text/html' },
      });
    }

    // Scene review page: /<scene-id>
    const sceneMatch = path.match(/^\/([a-z0-9-]+)$/);
    if (sceneMatch) {
      return new Response(renderPage(sceneMatch[1]), {
        headers: { 'Content-Type': 'text/html' },
      });
    }

    return new Response('Not found', { status: 404 });
  },
};
