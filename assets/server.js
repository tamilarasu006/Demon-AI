const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';

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
      model: parsed.model || 'gpt-4o-mini',
      messages: parsed.messages || [{ role: 'user', content: parsed.prompt || '' }],
      max_tokens: parsed.max_tokens || 1024,
      temperature: parsed.temperature !== undefined ? parsed.temperature : 0.7,
    });

    const options = {
      hostname: 'api.openai.com',
      port: 443,
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
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
    res.end(JSON.stringify({ status: 'ok', model: 'gpt-4o-mini', engine: 'openai' }));
    return;
  }

  // OpenAI proxy endpoint
  if (req.method === 'POST' && url === '/v1/chat/completions') {
    if (!OPENAI_API_KEY) {
      res.writeHead(500, corsHeaders({ 'Content-Type': 'application/json' }));
      res.end(JSON.stringify({ error: 'OPENAI_API_KEY not set on server' }));
      return;
    }
    proxyOpenAI(req, res);
    return;
  }

  // 404
  res.writeHead(404, corsHeaders({ 'Content-Type': 'application/json' }));
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`DEMON AI server running at http://localhost:${PORT}`);
  console.log(`OpenAI key: ${OPENAI_API_KEY ? 'SET ✓' : 'MISSING ✗'}`);
});
