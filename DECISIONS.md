# Architecture decisions & open questions

Decisions made this session, each with rationale and how to reverse it.
Items in **Part 2** need your call.

---

## Part 1 — Decisions made (challenge any of these)

### 1. Vanilla static site instead of Astro
The handoff proposed Astro but left the door open ("Astro rebuild via Action,
or pure client-side fetch"). The site is three views rendering committed JSON;
a no-build vanilla SPA means the daily Action only commits a JSON file — no
Node toolchain, no dependency updates, no build failures, instant deploys.
This best serves the project's own stated values ($0 forever, near-zero
maintenance). Chart.js is vendored (no CDN dependency).
*Reverse by*: porting `docs/` into an Astro project later; the JSON contract
doesn't change.

### 2. `zoneinfo` (stdlib) instead of `pytz`
`pytz` is legacy; `zoneinfo` is the standard-library replacement.
`tzdata` pip package supplies the database on Windows. Also switched
`US/Central` → `America/Chicago` (the canonical id).

### 3. Wikiquote: per-date subpage via MediaWiki API
Every QOTD lives at `Wikiquote:Quote of the day/{Month D, YYYY}` with clean
`|quote=` / `|author=` template params. Far more stable than scraping the
rendered main page (v1's approach, confirmed broken), and it works for any
past date, which backfill requires.

### 4. Merriam-Webster: per-date archive page as primary
`merriam-webster.com/word-of-the-day/YYYY-MM-DD` works for today *and* any
past date — one code path for live + backfill. RSS remains as fallback for
today's run.

### 5. Privacy model: personas in the repo, real names in a secret
**This is a deliberate upgrade over the handoff plan.** The handoff kept real
names in the source and only mapped personas at publish time — but free
GitHub Pages requires a public repo, which would have exposed the names list,
the group name, and `state.json` to anyone. Now: source, state, and all
published JSON contain only personas (Charlie, Frankie, Sasha, Robin, Jordan,
Riley — Set C, gender-ambiguous). Real names + the private chat header exist
only in gitignored `config/private.local.json` (local) or the
`PRIVATE_CONFIG_JSON` secret (Actions). The Telegram message gets real names;
the repo never does. Pre-push history was also rebuilt so no commit ever
contained them.
*To change persona names*: edit `config/personas.json` +
`config/private.local.json` + the secret, then re-run the backfill.

### 6. Date-seeded picks instead of OS randomness (deviation from handoff)
The handoff specified OS-level randomness for Song of the Day. Date-seeded
randomness is still uniform and unpredictable-in-practice, but it makes runs
idempotent: if the Action retries or you regenerate a day, the same person is
named — an OS-random pick could announce two different people for the same
day. Same logic for the history-event pick.
*Reverse by*: swapping `random.Random(seed)` for `random.SystemRandom()` in
`src/sections/song.py`.

### 7. ESPN endpoint corrections
MLB path is `sports/baseball/mlb` (v1's path 400s), City SC id is `21812`
(v1's 500s), status lives under `competitions[0]`, scores can be objects,
soccer upcoming needs `?fixture=true`. All verified by live probing; see
CHANGELOG.

### 8. Backfilled market headlines via the Wayback Machine
The WSJ Markets RSS feed is captured by the Internet Archive near-daily. For
a backdated day, we accept a snapshot from that day or the day before —
real headlines, no synthesis. Days with no capture (3 of 30) omit the
section honestly.

### 9. History section: tragedy de-prioritization (editorial default)
Wikipedia's "on this day" skews heavily toward disasters. When non-mass-
casualty events exist for a date, those are preferred; if not, anything goes.
The skip list (JFK, Pearl Harbor, etc.) and 30-year preference from the spec
remain. *Reverse by*: deleting `TRAGEDY_PATTERN` filtering in
`src/sections/history.py`.

### 10. Calendar badges map to game day, not report day
A report dated D contains the result of the game played on D-1. The archive
calendar colors day D-1 with that result, so a dot means "the Cardinals won
on this day," which is what a calendar reader expects.

---

## Part 2 — Decisions YOU need to make

1. **Persona names** — I defaulted to Set C (Charlie, Frankie, Sasha, Robin,
   Jordan, Riley) because it's gender-ambiguous. Sets A/B/D from the handoff
   are one config edit + backfill re-run away. The current real↔persona
   pairing is in `config/private.local.json` — review it.
2. **Site name** — defaulted to "The Gateway Almanac" (the handoff's leading
   candidate). Shown in the masthead, manifest, and `index.json`.
3. **GitHub repo name / URL obscurity** — recommend something like
   `gw-almanac-k7x2q9` (random suffix). Note honestly: a public repo is
   discoverable via GitHub search regardless of the Pages URL — the real
   protection is that nothing private is in it. If you want the repo itself
   private, GitHub Pages then requires a paid plan; the free alternative is
   Cloudflare Pages pointed at a private GitHub repo.
4. **Public vs private repo** — public + personas (current design) is the
   $0 path. Decide if that's acceptable or if you want the Cloudflare option.
5. **Telegram bot** — needs you to create it with @BotFather and add two
   secrets. SETUP.md walks through it (5 minutes).
6. **GitHub identity** — no global git user is configured on this machine;
   commits currently use a neutral local identity (`almanac-bot`). Run
   `gh auth login` when ready to push.
7. **Char limit behavior** — currently warns on stderr if the text exceeds
   2,500 chars but doesn't trim (reports run ~1,600–2,000). Want auto-trim?
8. **Sports facts review** — 135 entries are flagged "pending user review"
   in the JSON. Spot-check, especially date-keyed ones. Growing toward 366
   is an open task; the rotation handles any pool size meanwhile.
9. **2026-06-07 / 06-09 / 05-24 market sections** — genuinely no Wayback
   capture those days. Leave the gaps (honest) or backfill those three by
   hand from memory of the week's news? I'd leave them.
