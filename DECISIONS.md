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

## Part 2 — Decision log (updated after user review, 2026-06-10)

1. **Persona names — RESOLVED.** User wants male names keeping the real
   initials (M, J, D, P, E, A). Chosen: **Porter, Archie, Jonas, Eli,
   Dexter, Miles** — picked to avoid nickname-adjacency with the real names
   (no Pete/Jack/Evan/Danny/Martin; "Paul" → Porter and "Miles" → Max were
   swapped on user request). Remaining same-initial alternates if any feel
   off: Preston/Patrick · August/Abel · Jasper/Jude · Emmett/Ezra ·
   Duke/Drew · Murphy. Changing later = edit `config/personas.json` +
   `config/private.local.json` + secret, run `scripts/resync_personas.py`.
2. **Site name — "The Gateway Almanac" accepted for now.** Alternatives on
   file (all unindexed either way): *Mound City Almanac* (STL's 19th-century
   nickname — obscure to outsiders), *Confluence Daily* (the rivers),
   *Arch City Ledger*, *The Gateway Gazette*, *The Rivergate Register*; or
   zero-STL options: *The Split-Flap*, *The Morning Board*. One constant in
   `src/config.py` + masthead/manifest strings to change.
3. **Hosting — staying on GitHub Pages (public repo + personas).**
   Cloudflare Pages comparison for the record:
   - *Pros*: repo could stay private at $0; unlimited bandwidth; pick-your-
     own `*.pages.dev` subdomain (clean obscurity); deploys auto-trigger on
     the daily data commit; arguably faster CDN.
   - *Cons / extra stress*: one more account + dashboard to maintain;
     a GitHub-app authorization to keep healthy; build config to define
     once (trivial here: no build, output dir `docs`); deploy failures now
     happen in a second system you have to check; free tier caps at 500
     builds/month (daily commits ≈ 30 — fine, but a busy editing day counts
     against it).
   - *Verdict*: not needed unless the repo must go private. The current
     design keeps nothing private in the repo, so public GitHub Pages stays
     the zero-maintenance choice.
4. **Telegram — deferred.** The site now has a **📋 Copy for chat** button on
   every day view producing the exact iMessage-formatted text. Real names:
   open "⚙ chat names" once on your phone, enter the mapping — it's stored
   only in that browser's localStorage, never transmitted or committed.
   `delivery.py` stays dormant until/unless secrets are added.
5. **Sports facts — provisionally approved.** Goals recorded: uniqueness,
   no repeats, interesting, sports-related. Rotation guarantees no
   consecutive-day repeats; each general fact recurs ~3–4×/year ~98 days
   apart until the pool grows toward 366.
6. **Char limit — non-issue.** Warn-only stays (reports run ~1,300–2,000).
7. **Still open**: `gh auth login` + repo creation + Pages enablement
   (SETUP.md steps 1–2, minus the now-optional Telegram steps), facts
   deep-review later, three honest market gaps left as-is.
