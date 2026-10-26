# Five Letters: setting up on a new machine

This project is self-contained. Nothing here depends on the machine it was built on. Follow
these steps on any Mac or Linux box with Node 18 or newer, then read `CLAUDE.md` for the
full project context (decisions, code layout, gotchas, backlog).

## 1. Get the files

You received either `five-letters-handoff.zip` or `five-letters-bundle.md`.

**From the zip:**

```bash
unzip five-letters-handoff.zip && cd five-letters
```

The zip also contains `five-letters.gitbundle`, the complete git history. To restore it as a
proper repository instead of a plain folder:

```bash
git clone five-letters.gitbundle five-letters-repo && cd five-letters-repo
```

**From the single markdown bundle:** every file appears under a `### path/to/file` heading
in a fenced code block. Recreate each file at that path. A short script to do it
automatically is at the top of that bundle.

**If you have GitHub access as the owner:** the canonical repo is
https://github.com/DerekDimSum/five-letters (private). `git clone` it and skip the above.

## 2. Run it locally

```bash
npm run dev
```

Open http://localhost:8766. That is the game with a fake in-memory stats store and real
definition lookups. Add `?debug` to the URL to log analytics events to the console and get
`window.FiveLettersDebug` (includes `game().answer`, handy for testing a win).

There are no dependencies to install: the game is one HTML file, the dev server is plain
Node, the API functions use Node's built-in `fetch`.

## 3. Deploy

The project is a static site plus two serverless functions in `api/`. It is already shaped
for Vercel and needs no build step.

**Recommended, no CLI:** push the folder to a GitHub repo, then at https://vercel.com/new
import that repo. Framework preset "Other", leave build command and output directory empty.
Every later push to `main` deploys automatically.

**With the CLI:** `npx vercel deploy --prod --yes` from the project folder (needs a one-time
`npx vercel login`).

The existing production deployment is https://five-letters-phi.vercel.app under the owner's
`dim-sum-games` Vercel team, connected to the GitHub repo above. If you deploy elsewhere, the
game needs nothing configured; the two optional environment variables are described in
`README.md` (Upstash Redis for live comparison percentages).

Any other static host works for the game itself. Without the `api/` functions the end screen
shows the word-difficulty estimate instead of live percentages and skips the meaning line;
both degrade silently.

## 4. Regenerating word packs (optional)

The packs in `packs/` are ready to use. To rebuild them:

```bash
python3 -m venv .venv && .venv/bin/pip install wordfreq
.venv/bin/python scripts/build-packs.py
```

The builder reads `/usr/share/dict/words` (present on macOS; on Debian/Ubuntu install
`wamerican`) and, if present, `/usr/share/dict/propernames` (macOS only; the builder tolerates
its absence but will let more first names through). Full rules are in `WORD-PACK-SPEC.md`.

## 5. Embedding in a super app

Serve `index.html` and the `packs/` folder together from the same origin, point `STATS_API`
and `DEFINE_API` at wherever the functions are hosted if that is a different origin, and
inject `window.FiveLettersHost` before the page script. The contract is in `HOST-BRIDGE.md`.

## 6. Then

Read `CLAUDE.md`. It is the handoff from the previous Claude session: what the owner has
decided, what is verified and what is not, the known gaps, and the ranked backlog.
