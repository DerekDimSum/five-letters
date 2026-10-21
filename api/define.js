// Short definition of a word for the end screen, so non-native speakers learn
// something from every puzzle. Uses Datamuse (reliable, keyless) with the Free
// Dictionary API as a fallback, proxied so the game never calls a third party
// directly and results are cached at the edge for a day.
//
// GET /api/define?word=theme&lang=en -> { word, pos, definition } or 404

const POS = { n: 'noun', v: 'verb', adj: 'adjective', adv: 'adverb', u: '' };

async function withTimeout(url, ms) {
  const ctrl = new AbortController(); const t = setTimeout(() => ctrl.abort(), ms);
  try { return await fetch(url, { signal: ctrl.signal }); } finally { clearTimeout(t); }
}

async function fromDatamuse(word) {
  const r = await withTimeout(`https://api.datamuse.com/words?sp=${word}&md=d&max=1`, 3500);
  if (!r.ok) return null;
  const data = await r.json();
  const hit = Array.isArray(data) && data.find(d => d.word === word && Array.isArray(d.defs) && d.defs.length);
  if (!hit) return null;
  const [code, text] = hit.defs[0].split('\t');
  return { pos: POS[code] !== undefined ? POS[code] : code, definition: text };
}

async function fromFreeDictionary(word) {
  const r = await withTimeout(`https://api.dictionaryapi.dev/api/v2/entries/en/${word}`, 3500);
  if (!r.ok) return null;
  const data = await r.json();
  const entry = Array.isArray(data) && data[0];
  const meaning = entry && entry.meanings && entry.meanings.find(m => m.definitions && m.definitions.length);
  return meaning ? { pos: meaning.partOfSpeech || '', definition: meaning.definitions[0].definition } : null;
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const word = String((req.query && req.query.word) || '').toLowerCase();
  const lang = String((req.query && req.query.lang) || 'en').toLowerCase();
  if (!/^[a-z]{3,10}$/.test(word)) return res.status(400).json({ error: 'bad word' });
  if (lang !== 'en') return res.status(404).json({ error: 'no dictionary for this language yet' });
  let m = null;
  try { m = await fromDatamuse(word); } catch (e) {}
  if (!m) { try { m = await fromFreeDictionary(word); } catch (e) {} }
  if (!m || !m.definition) { res.setHeader('Cache-Control', 's-maxage=600'); return res.status(404).json({ error: 'not found' }); }
  let definition = String(m.definition).trim();
  definition = definition.charAt(0).toUpperCase() + definition.slice(1);
  if (definition.length > 160) definition = definition.slice(0, 157).replace(/\s+\S*$/, '') + '…';
  res.setHeader('Cache-Control', 's-maxage=86400, stale-while-revalidate=604800');
  return res.status(200).json({ word, pos: m.pos, definition });
};
