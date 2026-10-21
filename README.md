# Five Letters

A daily five-letter word game built as a single HTML file so it can drop into a super app's
WebView, with one small serverless function behind it for the "how you compared" line.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The whole game: markup, styles, logic and the embedded word pack. No build step. |
| `api/stats.js` | Vercel serverless function. Aggregates results per puzzle so the end screen can say "Faster than 62% of players". |
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

### Enable the live comparison line

Without a store the API returns 503 and the game silently falls back to its word-difficulty
estimate, so the deploy works with nothing else. To turn on real numbers:

1. In the Vercel project, open **Storage** and add an **Upstash Redis** database (free tier is fine).
2. Connect it to the project. Vercel sets `KV_REST_API_URL` and `KV_REST_API_TOKEN` automatically.
3. Redeploy.

The function also accepts `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` if you provision
Upstash directly. Keys expire after 400 days. There is no rate limiting yet; if the numbers ever
look gamed, put the route behind Vercel's firewall rules or add a per-IP cap.

## Word packs

The game ships with a small placeholder pack. Replace the JSON inside
`<script id="wordpack" type="application/json">` in `index.html` with a real pack. See
`WORD-PACK-SPEC.md` for the format and the rules for each list.

## Super app integration

Everything that touches the outside world goes through the `Host` object at the top of the
script in `index.html`: storage, haptics, share and the clock. Replace those four methods with
the host's JS bridge calls and nothing else changes. Theme follows the system by default and
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
