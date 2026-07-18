const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENAI_API_KEY = OPENROUTER_API_KEY; // alias used below

// OpenRouter base
const OR_HOST = 'openrouter.ai';
const OR_CHAT = '/api/v1/chat/completions';
const OR_MODEL = 'openai/gpt-4o-mini';

// ── serve a file ──────────────────────────────────────────────────────────────
function serveFile(res, filePath, contentType) {
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, corsHeaders({ 'Content-Type': 'text/plain' }));
      res.end('Not found');
    } else {
      res.writeHead(200, corsHeaders({ 'Content-Type': contentType }));
      res.end(data);
    }
  });
}

function corsHeaders(extra) {
  return Object.assign({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  }, extra);
}

// ── proxy to OpenAI ───────────────────────────────────────────────────────────
function proxyOpenAI(req, res) {
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    let parsed;
    try { parsed = JSON.parse(body); } catch(e) {
      res.writeHead(400, corsHeaders({ 'Content-Type': 'application/json' }));
      res.end(JSON.stringify({ error: 'Invalid JSON' }));
      return;
    }

    const payload = JSON.stringify({
      model: parsed.model || OR_MODEL,
      messages: parsed.messages || [{ role: 'user', content: parsed.prompt || '' }],
      max_tokens: parsed.max_tokens || 1024,
      temperature: parsed.temperature !== undefined ? parsed.temperature : 0.7,
    });

    const options = {
      hostname: OR_HOST,
      port: 443,
      path: OR_CHAT,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'http://localhost:8080',
        'X-Title': 'DEMON AI',
        'Content-Length': Buffer.byteLength(payload),
      }
    };

    const apiReq = https.request(options, (apiRes) => {
      let data = '';
      apiRes.on('data', chunk => { data += chunk; });
      apiRes.on('end', () => {
        // Pass the full OpenAI response including error status codes
        res.writeHead(apiRes.statusCode, corsHeaders({ 'Content-Type': 'application/json' }));
        res.end(data);
      });
    });

    apiReq.on('error', (e) => {
      res.writeHead(502, corsHeaders({ 'Content-Type': 'application/json' }));
      res.end(JSON.stringify({ error: { message: 'OpenAI API error: ' + e.message } }));
    });

    apiReq.write(payload);
    apiReq.end();
  });
}

// ── main server ───────────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, corsHeaders({}));
    res.end();
    return;
  }

  // Serve the HTML frontend
  if (req.method === 'GET' && (url === '/' || url === '/index.html')) {
    serveFile(res, path.join(__dirname, 'demon_terminal_demo_reel.html'), 'text/html; charset=utf-8');
    return;
  }

  // Health check
  if (req.method === 'GET' && url === '/health') {
    res.writeHead(200, corsHeaders({ 'Content-Type': 'application/json' }));
    res.end(JSON.stringify({ status: 'ok', model: OR_MODEL, engine: 'openrouter' }));
    return;
  }

  // OpenRouter chat proxy
  if (req.method === 'POST' && url === '/v1/chat/completions') {
    if (!OPENROUTER_API_KEY) {
      res.writeHead(500, corsHeaders({ 'Content-Type': 'application/json' }));
      res.end(JSON.stringify({ error: 'OPENROUTER_API_KEY not set on server' }));
      return;
    }
    proxyOpenAI(req, res);
    return;
  }

  // OpenAI TTS proxy — streams mp3 audio back to browser
  if (req.method === 'POST' && url === '/v1/tts') {
    if (!OPENAI_API_KEY) {
      res.writeHead(500, corsHeaders({ 'Content-Type': 'application/json' }));
      res.end(JSON.stringify({ error: 'OPENAI_API_KEY not set' }));
      return;
    }
    let body = '';
    req.on('data', c => { body += c; });
    req.on('end', () => {
      let parsed = {};
      try { parsed = JSON.parse(body); } catch(e) {}
      const payload = JSON.stringify({
        model: 'tts-1',
        input: parsed.text || '',
        voice: parsed.voice || 'nova',    // nova = warm friendly female
        response_format: 'mp3',
        speed: parsed.speed || 1.0,
      });
      const opts = {
        hostname: 'api.openai.com',
        port: 443,
        path: '/v1/audio/speech',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'Content-Length': Buffer.byteLength(payload),
        }
      };
      const apiReq = https.request(opts, (apiRes) => {
        if (apiRes.statusCode !== 200) {
          let errData = '';
          apiRes.on('data', c => { errData += c; });
          apiRes.on('end', () => {
            res.writeHead(apiRes.statusCode, corsHeaders({ 'Content-Type': 'application/json' }));
            res.end(errData);
          });
          return;
        }
        res.writeHead(200, corsHeaders({ 'Content-Type': 'audio/mpeg' }));
        apiRes.pipe(res);
      });
      apiReq.on('error', e => {
        res.writeHead(502, corsHeaders({ 'Content-Type': 'application/json' }));
        res.end(JSON.stringify({ error: e.message }));
      });
      apiReq.write(payload);
      apiReq.end();
    });
    return;
  }

  // 404
  res.writeHead(404, corsHeaders({ 'Content-Type': 'application/json' }));
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`DEMON AI server running at http://localhost:${PORT}`);
  console.log(`OpenRouter key: ${OPENROUTER_API_KEY ? 'SET ✓' : 'MISSING ✗'}`);
  console.log(`Model: ${OR_MODEL}`);
});
