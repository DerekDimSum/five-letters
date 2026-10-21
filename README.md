# Five Letters

A daily five-letter word game built as a single HTML file so it can drop into a super app's
WebView, with one small serverless function behind it for the "how you compared" line.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The whole game: markup, styles and logic. No build step. |
| `packs/` | Word lists, one JSON file per language, plus `index.json` listing them. The game fetches these at load. |
| `scripts/build-packs.py` | Rebuilds `packs/` from the system dictionary and word-frequency data, with solver-based difficulty scores. |
| `HOST-BRIDGE.md` | The interface a super app implements: storage, haptics, share, clock, analytics. |
| `api/stats.js` | Vercel serverless function. Aggregates results per puzzle so the end screen can say "Faster than 62% of players". |
| `api/define.js` | Serverless function. Returns a one-line definition of the answer (Datamuse, with the Free Dictionary API as fallback), cached at the edge. English only for now. |
| `scripts/dev-server.js` | Local server that serves the game and runs the API against an in-memory store. |
| `WORD-PACK-SPEC.md` | Requirements for building real word packs (English and other languages). |
| `vercel.json` | Clean URLs and a couple of headers. |

## Run locally

```bash
npm run dev
```

Then open http://localhost:8766. The dev server fakes the stats store in memory, so the live
comparison line works once 20 results exist for a puzzle. Seed some with:

```bash
for n in 0 3 3 4 4 4 4 5 5 5 6 2 3 4 4 4 5 5 3 3 4 4 6 0; do curl -s -o /dev/null -X POST -H 'Content-Type: application/json' -d "{\"pack\":\"en-placeholder\",\"puzzle\":1,\"result\":$n}" http://localhost:8766/api/stats; done
```

## Deploy

The project is a plain static site plus one function, so Vercel needs no configuration:

```bash
npx vercel --prod
```

Pushing to `main` deploys automatically through the GitHub integration. No CLI needed.

### Enable the live comparison line (optional)

Without a store the API returns 503 and the game silently falls back to its word-difficulty
estimate, so the deploy works with nothing else. To turn on real numbers:

1. In the Vercel project, open **Storage** and add an **Upstash Redis** database (free tier is fine).
2. Connect it to the project. Vercel sets `KV_REST_API_URL` and `KV_REST_API_TOKEN` automatically.
3. Redeploy.

The function also accepts `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` if you provision
Upstash directly. Keys expire after 400 days. There is no rate limiting yet; if the numbers ever
look gamed, put the route behind Vercel's firewall rules or add a per-IP cap.

## Word packs

Packs live in `packs/<id>.json` and are listed in `packs/index.json`; players pick one in
settings. English is built from common words validated against the macOS dictionary. Malay,
Indonesian and Filipino are frequency-only lists marked **beta** until a native speaker reviews
them. To rebuild:

```bash
python3 -m venv .venv && .venv/bin/pip install wordfreq && .venv/bin/python scripts/build-packs.py
```

See `WORD-PACK-SPEC.md` for the format and the rules for each list.

## Super app integration

Inject `window.FiveLettersHost` before the game script and the game routes storage, haptics,
share, the clock and analytics through it. Every method is optional. The full contract, haptic
kinds and the analytics event list are in `HOST-BRIDGE.md`. Theme follows the system by default and
can be forced with `data-theme="light|dark"` on the root element.

If the game is served from a different origin than the API, set `STATS_API` in `index.html` to
the full URL. The function already sends permissive CORS headers.

## Features

- Daily word by local date, deterministic across devices; practice mode with separate stats;
  archive of past puzzles.
- Correct duplicate-letter scoring, hard mode, high contrast, reduced-motion support.
- Resume mid-row after a reload; versioned local storage.
- Streaks with a streak freeze earned every seven daily games.
- End screen with a comparison line: live percentile when there is enough data, word-difficulty
  estimate otherwise. Share card via native share sheet or clipboard.
- Tap a tile to edit it, swipe left to clear the row, hold backspace to delete fast, optional
  unused-letters strip.
- No onboarding popup. A one-line hint under the empty grid, a colour legend after the first
  reveal, and one sentence on the first end screen; each shows once.
- Share card: a rendered PNG with the grid, result and comparison line, sent through the host
  or the Web Share API, with text and clipboard fallbacks.
- End screen shows the word's meaning, a one-line insight about how the solve went, streak
  milestones and personal bests, and confetti scaled to how fast the solve was.
- Daily words come from the most common part of each list (`dailyPool`); practice uses all of
  it. British, Singlish, Australian and Indian English spellings are accepted as guesses.
- Accessible: reveals are announced to screen readers, keys describe their state, sheets trap
  and restore focus.
