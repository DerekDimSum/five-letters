# Host bridge contract

The game runs in any browser on its own. Inside a super app, the host can inject one object
**before** the game script runs, and the game will route storage, haptics, sharing, time and
analytics through it. Every method is optional: anything missing falls back to the browser.

```js
window.FiveLettersHost = {
  storage: {                       // optional. Default: localStorage
    get(key)  { return string | null },
    set(key, value) {}             // value is a JSON string, up to ~50 KB per key
  },
  haptic(kind) {},                 // optional. kind: 'tap' | 'tick' | 'error' | 'success'
  share({ text, image }) {},       // optional. image is a PNG data: URL or null. Return a Promise;
                                   // reject with an Error named 'AbortError' if the user cancels
  now() { return Date.now() },     // optional. Server-trusted clock, if the host has one
  track(event, props) {},          // optional. Analytics, see events below
  userId() { return 'abc' }        // reserved for v4 (friends, leaderboards). Not read yet
};
```

The game reads the object once at load, so inject it synchronously in the WebView before
`index.html` executes (for example with `evaluateJavascript` on page start, or a script tag
placed above the game's own script if the host wraps the page).

## Haptic kinds

| kind | When | Suggested native feedback |
|---|---|---|
| `tap` | Every on-screen key press, tile tap, row clear | Light impact |
| `tick` | A row finishes revealing without ending the game | Light or selection changed |
| `error` | Rejected guess (not a word, too short, hard-mode rule), a lost game | Notification error |
| `success` | Solved | Notification success |

If `haptic` is missing, the game uses the Vibration API on Android and the iOS 17.4+ switch
tap on iPhone. Players can turn haptics off in settings; the game then never calls `haptic`.

## Share

`share` receives the plain-text result (emoji grid, comparison line, streak) and, when the
canvas rendered successfully, a 1080×1350 PNG share card as a data URL. Show the native share
sheet with the image attached and the text as the caption. Resolve when the sheet closes.

If `share` is missing, the game uses the Web Share API with the image file when the browser
allows it, text-only otherwise, and finally copies the text to the clipboard.

## Analytics events

All events carry `pack` (word list id) where relevant. Modes are `daily`, `practice`, `archive`.

| event | props | fires |
|---|---|---|
| `app_open` | `pack, puzzle, status, bridge` | once per load. `status` is `playing`, `won` or `lost` for today's puzzle |
| `game_start` | `mode, puzzle, pack` | first guess submitted in a game |
| `guess_submit` | `mode, n` | each accepted guess; `n` is the guess number |
| `game_finish` | `mode, won, guesses, puzzle, pack` | game ends |
| `share` | `mode, result, image` | Share tapped. `result`: `shared`, `copied`, `cancelled`, `failed` |
| `practice_start` | `pack` | a new practice word is dealt from the end screen |
| `pack_switch` | `from, to` | language changed in settings (page reloads after) |
| `setting_change` | `key, value` | hard mode, contrast, unused letters, haptics, theme |

Without a bridge, events are dropped unless the page is opened with `?debug`, which logs
them to the console.

## Storage keys

- `fiveletters.pack` — the chosen word list id.
- `fiveletters.settings` — settings shared across word lists.
- `fiveletters.<dailyPackId>` — the daily pack's games, archive, stats and practice games for
  every practice list (`practiceGames`, keyed by pack id). Versioned by a `schema` field.

Keys are plain strings; values are JSON strings. The host can namespace them per user.

## Theme

The game follows `prefers-color-scheme`. To force a theme, set `data-theme="light"` or
`data-theme="dark"` on `<html>` before load, or let the player choose in settings.
