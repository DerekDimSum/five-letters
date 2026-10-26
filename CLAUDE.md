# Five Letters: handoff notes for Claude

Read this first. It is the whole context a new session needs: what the project is, where it
lives, the decisions already made and why, how to run and ship it, what is verified and what
is not, and what the owner wants next. The other docs (README.md, HOST-BRIDGE.md,
WORD-PACK-SPEC.md) cover their own areas in more detail and are kept current.

## What this is

A daily five-letter word game (a Wordle-style game) built as one HTML file plus two small
serverless functions, designed to be embedded in a super app's WebView and also playable on
the open web. Owner: Derek (GitHub DerekDimSum, Vercel team dim-sum-games, based in
Singapore, APAC audience).

| | |
|---|---|
| Repo | https://github.com/DerekDimSum/five-letters (private) |
| Live | https://five-letters-phi.vercel.app (also five-letters-dim-sum-games.vercel.app) |
| Deploys | Automatic on every push to `main` through the Vercel GitHub integration. **Never needs the Vercel CLI or dashboard.** |
| Local folder | `~/Claude/five-letters` |
| Shared preview link | https://claude.ai/artifact/GhAmF1byVkkMjSojrYbJ4e (a Claude artifact copy, see "Publishing the artifact") |

## Owner's standing decisions (do not relitigate)

- **Daily puzzle is English only.** Other languages and the easy four-letter list are
  practice-only, chosen with chips above the grid in practice mode.
- **No ads, no gating.** The daily word is free and instant.
- **No friends, leaderboards or head-to-head yet.** Comparison against "others" is an
  anonymous aggregate only. `userId()` in the bridge is reserved, not read.
- **Keep it simple.** Onboarding is inline, not a popup. One screen for the end screen.
- **No Vercel interaction.** Push to GitHub and it deploys. The optional Upstash store for
  live percentages was offered and declined for now; the game works without it.
- Delight means noticing something specific about what the player did and saying it back.
  Generic praise reads as filler.

## Layout

| Path | What |
|---|---|
| `index.html` | The whole client: markup, CSS tokens, game logic, host adapter. No build step. ~70 KB. |
| `packs/index.json` | Manifest of word lists. Fields: `id, name, short, language, file, daily, practiceOnly, beta`. Exactly one entry has `daily: true`. |
| `packs/en.json` | Daily pack: 1,691 answers ordered most-common first, `dailyPool: 1200` (daily draws from the first 1,200; practice uses all), 8,055 extra accepted guesses, per-answer `difficulty` (expected guesses from a solver). |
| `packs/en-easy.json` | Four-letter English, practice only, 900 answers. |
| `packs/ms.json`, `id.json`, `fil.json` | Beta Malay, Indonesian, Filipino: 450 answers each, frequency-derived, not reviewed by native speakers. |
| `scripts/build-packs.py` | Regenerates all packs. Needs `pip install wordfreq`, uses `/usr/share/dict/words` and `propernames` (macOS). Runs in about a minute. |
| `scripts/dev-server.js` | Local server on :8766 serving the game plus both API routes against an in-memory fake Redis. `npm run dev`. |
| `api/stats.js` | Aggregates results per puzzle (HINCRBY in Upstash-compatible Redis REST). Returns 503 without `KV_REST_API_URL`/`KV_REST_API_TOKEN`; the client then shows a difficulty estimate instead. |
| `api/define.js` | One-line definition of the answer. English: Datamuse, then Free Dictionary, then Wiktionary. ms/id/fil: Wiktionary (fil maps to Wiktionary `tl`). Edge-cached a day. |
| `vercel.json` | `cleanUrls` and a nosniff header. Nothing else needed. |
| `HOST-BRIDGE.md` | Contract for `window.FiveLettersHost` (storage, haptic, share, now, track) and the analytics event list. |
| `WORD-PACK-SPEC.md` | Pack schema, list rules, per-language notes, delivery checklist. |

## How the client is organised (index.html)

Single async IIFE. Order of sections in the script:

1. `Bridge`/`Host`: the only code that touches the outside world. Storage, haptics
   (bridge, then Android Vibration API, then the iOS switch-tap trick), share (bridge, then
   Web Share with the PNG card, then text, then clipboard), clock, `track`.
2. Pack loading: `fetchPack`, `loadPackJson` (manifest, picks the `daily` entry),
   `normalizePack` (validates words, builds the deterministic shuffled daily `order` from the
   `dailyPool`, keeps `all` for practice, letter frequencies for the difficulty fallback).
   `PACK` and `L` are mutable: `DAILY_PACK` is fixed, practice may swap `PACK` and rebuild the
   board via `buildBoard(len)`.
3. Store: `fiveletters.<dailyPackId>` holds `daily`, `archive`, `practiceGames` (keyed by
   pack id), `stats.daily`, `stats.practice`, `settings`. `fiveletters.settings` mirrors
   settings globally. Schema versioned (`SCHEMA = 1`, `migrate()` stub).
4. Pure logic: `score` (two-pass, handles duplicate letters), `keyStates`,
   `hardModeViolation`, `expectedGuesses`, `compareLine` (templated copy, picked by puzzle
   number), `insightLine`.
5. Modes: `setMode('daily' | 'practice' | 'archive', arg, packId)` is async because practice
   may fetch a pack. `loadDaily` archives yesterday's game on rollover.
6. Rendering: `render()` is a function of state; `renderCoach` (onboarding hint and legend,
   once per player), `renderChips`, reveal animation in `submit()`.
7. Sheets: stats (compact result view by default, "Show my stats" expands), settings,
   archive, help. `openSheet`/`closeSheets` manage focus; Tab is trapped.
8. Share card: `shareImage()` draws a 1080×1350 PNG on canvas from theme tokens.
9. Boot: `applyTheme`, `setMode('daily')`, `track('app_open')`, `?debug` exposes
   `window.FiveLettersDebug = { shareImage, shareText, game(), pack(), setMode }` and logs
   analytics to the console.

CSS is token-based (`:root` light, dark via media query guarded by
`:root:not([data-theme="light"])` and again under `[data-theme="dark"]`), plus
`data-contrast="high"` and `data-text="large"`. `[hidden]{display:none!important}` is
declared explicitly; component `display` rules would otherwise beat the attribute.

## Running and testing

```bash
npm run dev            # http://localhost:8766, fake stats store, real definition lookups
```

Open `http://localhost:8766/?debug`. In the console, `FiveLettersDebug.game().answer` gives
the current answer, so a win can be played deliberately. Seed the fake stats store to see the
live comparison line (needs 20+ results for one puzzle):

```bash
for n in 0 3 3 4 4 4 4 5 5 5 6 2 3 4 4 4 5 5 3 3 4 4 6 0; do curl -s -o /dev/null -X POST -H 'Content-Type: application/json' -d "{\"pack\":\"en\",\"puzzle\":2,\"result\":$n}" http://localhost:8766/api/stats; done
```

Syntax-check the inline script without a browser:

```bash
python3 -c "import re;open('/tmp/g.js','w').write(re.findall(r'<script>(.*?)</script>',open('index.html').read(),re.S)[-1])" && node --check /tmp/g.js
```

Previous sessions tested in the Claude desktop browser pane at phone width (375×812). Note:
`preview_start` there launched the server from a stale folder once; running
`node scripts/dev-server.js` directly from the project folder was the fix. Screenshots from
that pane often lag a frame; verify state through the DOM (`javascript_tool`) rather than
pixels.

## Shipping

```bash
git add -A && git commit -m "..." && git push origin main   # deploys in ~15 s
```

Confirm with a cache-busted fetch; Vercel's edge can serve a stale 404 for a path probed
before the deploy finished:

```bash
curl -s "https://five-letters-phi.vercel.app/?r=$RANDOM" | grep -c packChips
```

Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` (or the
current model's attribution line).

### Publishing the artifact

The claude.ai artifact is a copy of `index.html` without the document skeleton (the Artifact
tool wraps it). Build it by taking `<title>`, the `claude:viewport-fit-sides` meta, the font
`<link>`, the `<style>` block, then the `<body>` inner HTML, and publish to the URL above
with the `packs/*.json` files attached as `files` (relative `fetch('packs/index.json')` works
there). The artifact cannot reach `/api/*`, so comparisons fall back to the estimate and no
definitions show; that is expected.

## What is verified and what is not

Verified in a desktop browser at phone width, fresh storage, both themes: onboarding hint and
legend, tile editing, reveal, win with confetti, six-guess loss, archive after midnight
rollover, practice chips including the four-letter board, pack switching with separate saved
games, compact end screen, "Day 1" wording, larger text, share card PNG rendering and the
clipboard fallback, screen-reader announcements, focus trap, every analytics event, definitions
in all four languages, the stats API with seeded data.

Not verified: anything on a real phone. Specifically iOS haptics (the switch-tap trick needs
iOS 17.4+ and fires only synchronously inside a tap; the owner initially felt nothing before
that fix and has not confirmed since), the share sheet with the PNG attached, VoiceOver, and
confetti frame rate on low-end Android.

## Known gaps and gotchas

- The daily answer is derivable from the pack file in the browser. Fine until comparisons or
  friends matter; a `/api/word` endpoint with local fallback is the planned fix.
- `api/stats.js` has no rate limiting. If live numbers are ever enabled and look gamed, put
  the route behind Vercel firewall rules.
- Beta language packs still contain some names and loanwords despite a blocklist. They need a
  native speaker's pass. Filipino is the weakest.
- The four-letter easy pack has had one pass for rude words; worth another skim before kids
  play it.
- Changing a pack's `id` resets players' storage for it. Changing `dailyPool` or the answer
  order changes today's word for everyone.
- The Google Font (Outfit) loads from the network with a system fallback. For a strict
  offline bundle inline it or drop it.
- Hard mode also locks grey keys, which is stricter than Wordle's. Panel players found that
  confusing; renaming it "Strict mode" or matching Wordle is an open choice.
- The free dictionary API behind definitions has been flaky (530s); Datamuse is primary for
  that reason.

## Player panel feedback still open

From two rounds of a simulated 20-player APAC panel. Done: inline onboarding, meaning line,
regional spellings accepted, friendlier daily pool, taller keys, one-screen end screen, varied
comparison copy, larger text, freeze count on the streak tile, easy pack, practice-only
language lists.

Still open, roughly in priority order:

1. Daily reminder (needs the host app's push notifications).
2. Non-Latin packs (Thai, Vietnamese, Japanese, Korean) need board and keyboard support for
   other scripts; out of scope so far.
3. Native-speaker review of the Malay, Indonesian and Filipino lists.
4. Insight lines land when specific and fall flat when generic ("Quick and clean"); more
   specific cases would help.
5. Legend after the first reveal appears under the board while players look at the keyboard;
   some missed it.
6. Server-side daily word; rate limiting on the stats route.
7. Live percentages: optional Upstash Redis store via Vercel Storage, sets the two env vars
   automatically. Declined for now.

## Conventions the owner is used to

- Work is summarised in plain prose, no headers in short replies, lead with the outcome.
- Each shipped change: commit, push, confirm live, republish the artifact, then report what
  was verified and what was not, honestly.
- When asked "what would the panel say" or "what next", give a ranked opinion, then build on
  a yes.
