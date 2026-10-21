// Aggregate results per puzzle so the end screen can say how a player compared.
// Storage: any Upstash-compatible Redis REST endpoint. On Vercel, adding the
// Upstash Redis integration (Marketplace > Storage) sets KV_REST_API_URL and
// KV_REST_API_TOKEN automatically. Without them this returns 503 and the game
// falls back to its word-difficulty estimate.
//
// GET  /api/stats?pack=en&puzzle=12          -> { count, dist: [lost, 1, 2, 3, 4, 5, 6] }
// POST /api/stats { pack, puzzle, result }   -> records result (1-6 = solved in n, 0 = lost), returns the same

const STORE_URL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const STORE_TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
const TTL_SECONDS = 60 * 60 * 24 * 400;

async function redis(command) {
  const r = await fetch(STORE_URL, {
    method: 'POST',
    headers: { Authorization: `Bearer ${STORE_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  });
  if (!r.ok) throw new Error(`store responded ${r.status}`);
  const data = await r.json();
  if (data.error) throw new Error(data.error);
  return data.result;
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET' && req.method !== 'POST') return res.status(405).json({ error: 'method not allowed' });
  if (!STORE_URL || !STORE_TOKEN) return res.status(503).json({ error: 'stats store not configured' });

  let body = req.body || {};
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  const q = req.method === 'GET' ? (req.query || {}) : body;
  const pack = String(q.pack || '').slice(0, 40);
  const puzzle = parseInt(q.puzzle, 10);
  if (!/^[a-z0-9-]+$/.test(pack) || !(puzzle > 0 && puzzle < 100000)) return res.status(400).json({ error: 'bad pack or puzzle' });
  const key = `fl:${pack}:${puzzle}`;

  try {
    if (req.method === 'POST') {
      const result = parseInt(q.result, 10);
      if (!(result >= 0 && result <= 6)) return res.status(400).json({ error: 'result must be 0 (lost) or 1-6' });
      await redis(['HINCRBY', key, String(result), 1]);
      await redis(['EXPIRE', key, TTL_SECONDS]);
    }
    const flat = (await redis(['HGETALL', key])) || [];
    const dist = Array(7).fill(0);
    for (let i = 0; i + 1 < flat.length; i += 2) {
      const k = parseInt(flat[i], 10);
      if (k >= 0 && k <= 6) dist[k] = parseInt(flat[i + 1], 10) || 0;
    }
    const count = dist.reduce((a, b) => a + b, 0);
    return res.status(200).json({ pack, puzzle, count, dist });
  } catch (e) {
    return res.status(502).json({ error: 'store unavailable' });
  }
};
