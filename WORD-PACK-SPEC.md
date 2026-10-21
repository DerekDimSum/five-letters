# Word pack requirements

A word pack is one JSON file in `packs/`, named `<id>.json`, and listed in `packs/index.json`:

```json
[
  { "id": "en", "name": "English", "language": "en", "file": "packs/en.json" },
  { "id": "ms", "name": "Bahasa Melayu", "language": "ms", "file": "packs/ms.json", "beta": true }
]
```

The first entry is the default. `beta: true` shows a "(beta)" tag in the language picker.
`scripts/build-packs.py` generates the current packs; a hand-built pack just needs to follow
the schema below and be added to the manifest.

## Schema

```json
{
  "id": "en",
  "name": "English",
  "language": "en",
  "version": 1,
  "wordLength": 5,
  "alphabet": "abcdefghijklmnopqrstuvwxyz",
  "keyboard": ["qwertyuiop", "asdfghjkl", "zxcvbnm"],
  "epoch": "2026-10-21",
  "answers": ["about", "above", "..."],
  "guesses": ["aahed", "aalii", "..."],
  "difficulty": { "about": 3.6, "above": 4.1 }
}
```

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Short slug, lowercase, letters/digits/hyphens. Used as the storage key and the shuffle seed, so changing it resets players' saved games and stats for that pack. |
| `name` | yes | Display name shown in settings. |
| `language` | yes | BCP 47 tag, e.g. `en`, `ms`, `id`, `tl`, `zh-Latn`. |
| `version` | yes | Integer. Bump when the lists change. Bumping it does **not** reshuffle the answer order, so existing puzzle numbers stay stable. |
| `wordLength` | yes | Integer, 4 to 8. All words must be exactly this length. V1 is tuned for 5. |
| `alphabet` | yes | Every letter that may appear in any word, lowercase, in the order you want the hard-mode "letters left" list to use. Must cover every character in `answers` and `guesses`. |
| `keyboard` | yes | Two to four strings, one per row. Must contain every letter in `alphabet` exactly once. The game adds Enter and Backspace to the last row. |
| `epoch` | yes | `YYYY-MM-DD`, the date of puzzle #1 in the player's local time. |
| `answers` | yes | The pool a daily word is drawn from. |
| `guesses` | yes | Additional accepted words that are never used as answers. Everything in `answers` is automatically accepted, so do not repeat them here. |
| `difficulty` | no | Map of answer word to expected number of guesses as a float. If missing, the game estimates difficulty from letter frequency. |

Either list may be given as an array of strings, as one space-separated string
(`"about above abuse ..."`), or as one concatenated string with no separators
(`"aboutaboveabuse..."`). The concatenated form is the smallest but a single wrong-length
word shifts every word after it, so only use it if your build step validates lengths first.
The game accepts all three.

## Rules that apply to both lists

- Lowercase, UTF-8, NFC-normalised. No whitespace, hyphens, apostrophes, digits or punctuation.
- Every character must be in `alphabet`.
- Exactly `wordLength` characters. Count code points, not bytes, for non-ASCII letters.
- No duplicates within a list and no overlap between lists.
- No slurs or words that would be unacceptable to show as "the answer was". Use a
  blocklist and apply it to both lists, since a blocked word being accepted as a guess
  is nearly as bad as it being the answer.
- Order does not matter. The game shuffles `answers` deterministically using `id`, so an
  alphabetical file is fine and produces a non-alphabetical daily sequence.

## `answers` (the daily pool)

Target size: 2,000 to 2,500 for English. Minimum 400 so a year of daily puzzles never
repeats. The bar is "a typical adult native speaker would recognise it instantly".

Include:
- Common nouns, verbs, adjectives and adverbs in everyday use.
- Words with repeated letters. Keep roughly the natural proportion, around 25 to 30%.

Exclude:
- Proper nouns, brand names, place names, demonyms.
- Plurals formed with s or es, and third-person verb forms with s (`cakes`, `walks`).
  Irregular plurals like `teeth` or `women` are fine.
- Past tenses and participles formed with ed unless the word is also a common standalone
  adjective (`tired` and `fixed` are fine; `baked` is not).
- Abbreviations, initialisms, Roman numerals.
- Archaic, dialect, jargon, Scrabble-only and crossword-only words.
- Variant spellings outside the pack's dialect. For `en` pick one of US or UK spelling
  (`color` vs `colour`) and use it consistently; put the other spelling in `guesses`.
- Anything crude, medical-anatomical in a way people would not want on a share card, or
  tied to a tragedy.

## `guesses` (accepted but never the answer)

Target size: 10,000 to 13,000 for English. The bar is "it is a real word in a standard
dictionary". Being obscure is fine here.

Include:
- Plurals, verb forms, comparatives, past tenses.
- Less common words, technical words, archaic words still in dictionaries.
- Both US and UK spellings.
- Common informal words that have reached mainstream dictionaries.

Exclude:
- Proper nouns and abbreviations, same as above.
- Slurs and the blocklist.
- Anything a player would reasonably contest as not a word. Lean on one named source
  dictionary per language and record which one in the pack's commit message or README.

## `difficulty` (optional but recommended)

One float per answer word, the expected number of guesses a competent player needs.
Range in practice is about 2.8 to 5.5. The game uses this for the "how you compared"
line on the end screen when no live aggregate data is available.

Suggested method: run a simple solver that, from a fixed good opening word, repeatedly
picks the candidate with the best letter-frequency score among words still consistent
with all feedback, and record the number of guesses it takes to reach each answer.
Average across three different opening words. This takes a few seconds for an English
list. Words the solver fails to reach within six guesses get 6.0.

If you skip this field the game computes a rough estimate from letter frequency and a
repeated-letter penalty. It is noticeably worse than a solver-based score, so include it
if at all possible.

## Per-language notes

- **Malay / Indonesian (`ms`, `id`):** Latin alphabet, no diacritics needed. Five-letter
  words are plentiful. Decide whether affixed forms (`makan` yes, `dimakan` no at 5 letters
  anyway) count as separate words and be consistent. Keep the two languages as separate
  packs even where lists overlap heavily, so the daily sequence is distinct.
- **Tagalog / Filipino (`tl`):** Include `ng` as two letters, not one. Decide whether to
  include `ñ`; if yes, add it to `alphabet` and give it a keyboard key. Most packs omit it.
- **Singlish or themed packs:** Treat these as `guesses`-heavy packs with a small curated
  `answers` list of 400 to 600, since the recognisable pool is smaller. Theme packs
  (food, places) should set `name` to the theme and may reuse `language: "en"`.
- **Any non-Latin script:** Out of scope for v1. The board and keyboard assume one
  glyph per letter and a Latin-style keyboard layout.

## Delivery checklist

Before handing over a pack, run a check that confirms:

1. Valid JSON, all required fields present, `wordLength` matches every word.
2. Every character of every word is in `alphabet`; `keyboard` contains each letter exactly once.
3. No duplicates within or across `answers` and `guesses`.
4. No blocklist hits in either list.
5. `answers` count is at least 400; `guesses` count is at least 3 times `answers` for a general-language pack.
6. `difficulty` keys, if present, are all in `answers`.
7. File size: under 200 KB raw for a full English pack. Use the concatenated-string form if you are over.

The game validates length, alphabet and duplicates at load and drops offending words with a
console warning, so a slightly dirty pack still runs, but the check above is what makes it
shippable.
