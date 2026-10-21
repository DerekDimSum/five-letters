// Local dev server: serves the static game and runs api/stats.js against an
// in-memory fake of the Upstash Redis REST API, so the live comparison line can
// be exercised without a real store. Run with: npm run dev  (http://localhost:8766)
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT) || 8766;
const ROOT = path.join(__dirname, '..');
process.env.KV_REST_API_URL = `http://127.0.0.1:${PORT}/__fake-redis`;
process.env.KV_REST_API_TOKEN = 'dev';
const handler = require(path.join(ROOT, 'api', 'stats.js'));
const define = require(path.join(ROOT, 'api', 'define.js'));

const hashes = new Map();
function fakeRedis(cmd) {
  const [op, key, ...args] = cmd;
  if (op === 'HINCRBY') { const h = hashes.get(key) || {}; h[args[0]] = (h[args[0]] || 0) + Number(args[1]); hashes.set(key, h); return h[args[0]]; }
  if (op === 'EXPIRE') return 1;
  if (op === 'HGETALL') { const h = hashes.get(key) || {}; return Object.entries(h).flatMap(([k, v]) => [k, String(v)]); }
  throw new Error('unsupported ' + op);
}

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.md': 'text/plain; charset=utf-8', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml' };

function readBody(req) { return new Promise(r => { let b = ''; req.on('data', c => b += c); req.on('end', () => r(b)); }); }

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (url.pathname === '/__fake-redis') {
    const cmd = JSON.parse(await readBody(req));
    try { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify({ result: fakeRedis(cmd) })); }
    catch (e) { res.statusCode = 400; res.end(JSON.stringify({ error: e.message })); }
    return;
  }
  if (url.pathname === '/api/define') {
    const vreq = { method: req.method, query: Object.fromEntries(url.searchParams) };
    const vres = { status(c) { res.statusCode = c; return vres; }, setHeader: (k, v) => res.setHeader(k, v), json(o) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)); }, end: () => res.end() };
    return define(vreq, vres);
  }
  if (url.pathname === '/api/stats') {
    const raw = await readBody(req);
    const vreq = { method: req.method, query: Object.fromEntries(url.searchParams), body: raw ? JSON.parse(raw) : {} };
    const vres = {
      status(c) { res.statusCode = c; return vres; },
      setHeader: (k, v) => res.setHeader(k, v),
      json(o) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)); },
      end: () => res.end(),
    };
    return handler(vreq, vres);
  }
  let file = path.join(ROOT, decodeURIComponent(url.pathname));
  if (url.pathname === '/' ) file = path.join(ROOT, 'index.html');
  if (!file.startsWith(ROOT)) { res.statusCode = 403; return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.statusCode = 404; return res.end('not found'); }
    res.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
    res.end(data);
  });
}).listen(PORT, '127.0.0.1', () => console.log(`dev server on http://localhost:${PORT}`));
