# Changelog

## v2.4 — 2026-06-12

- Schedule hardened around the user's hard deadline (report ready by
  8:45 AM CT): four cron attempts an hour apart (10:20-13:20 UTC =
  5:20-8:20 AM CT summer / 4:20-7:20 winter), guard window widened to
  4:00-11:59 CT, dedupe unchanged (first attempt to land publishes,
  the rest no-op).

## v2.3 — 2026-06-12

- **Fix: morning run never fired.** GitHub's top-of-hour cron slots are
  congested (the 13:00 UTC schedule was dropped entirely on 06-12, and a
  06-11 cron arrived 3.5 h late only for the strict hour==08 guard to
  skip it). Crons moved to 12:50/13:50 UTC (~7:50 AM CT), the guard now
  accepts a 7:45–11:59 CT window, and a dedupe check (today's report file
  already committed?) guarantees at most one publish per day. Runner also
  rebases before pushing to avoid race failures.

## v2.2 — 2026-06-11

- Personas: "Miles" → **Max** (user request; earlier "Paul" → Porter).
  Reports/state/index resynced; real-person assignments unchanged
  (seed-stable).
- Schedule moved **9:00 → 8:00 AM Central** (crons now 13:00/14:00 UTC,
  guard hour 08) so the report is ready before anyone wants to share it.

## v2.1 — 2026-06-10 (decision round)

- **Personas renamed** per user: male names keeping real initials —
  Paul, Archie, Jonas, Eli, Dexter, Miles. All 30 published reports and
  state.json resynced via new `scripts/resync_personas.py` (pure-local,
  no API calls; picks are seed-stable so real-person assignments held).
- **📋 Copy for chat** button on every day view (`docs/js/share.js`):
  rebuilds the exact iMessage-formatted text from the day's JSON in the
  browser. Optional "⚙ chat names" panel maps personas to real display
  names via localStorage only — nothing private is transmitted, stored
  server-side, or committed. Verified byte-equivalent with the Python
  renderer. Telegram remains optional/dormant.
- `index.json` now carries the persona roster for the settings panel;
  service worker bumped to ga-v2.
- DECISIONS.md Part 2 updated: persona/site-name/hosting/Telegram/facts/
  char-limit decisions logged, Cloudflare Pages trade-offs recorded.

## v2 — 2026-06-10 (this session)

Full build-out from the v1 scaffold: pipeline fixes, privacy model, 30-day
backfill, static site, and GitHub automation.

### Pipeline fixes (all verified against live APIs)
- **ESPN MLB endpoint**: `sports/mlb/...` returns HTTP 400 → corrected to
  `sports/baseball/mlb/...` (NHL likewise `sports/hockey/nhl`).
- **City SC team id**: v1's `17012` returns HTTP 500 → correct id is `21812`
  (verified via the MLS team directory endpoint).
- **Game status**: lives at `competitions[0].status`, not `event.status`
  (v1 found 0 completed games because of this).
- **Scores**: schedule endpoint returns objects (`{value, displayValue}`),
  not strings; both shapes now handled, plus the `winner` flag and soccer
  draws (`D 1-1`).
- **Soccer fixtures**: team schedule endpoint returns past results only;
  upcoming games need a second call with `?fixture=true`.
- **Wikiquote parser**: v1's main-page tilde scraping found nothing
  (confirmed broken). Replaced with the per-date subpage
  (`Wikiquote:Quote of the day/June 10, 2026`) via the MediaWiki API —
  structured `|quote=`/`|author=` wikitext params, works for any date.
- **Word of the Day**: primary source is now the per-date archive page
  (`merriam-webster.com/word-of-the-day/YYYY-MM-DD`, works for today and
  past dates); RSS is the fallback.
- **Windows fixes**: `strftime %-d/%-I` (POSIX-only) replaced with a
  cross-platform formatter; stdout reconfigured to UTF-8 (cp1252 consoles
  crash on emoji).
- **Backdated "next game"**: a since-completed game on/after a backdated
  report date is still that morning's "next game" (was showing a game
  weeks later).
- **Spotlight**: v1 built a seeded RNG but accidentally used the global
  `random.choice` — rewritten with a pure, week-seeded pick that excludes
  the previous week's persona.

### New
- **Privacy model**: repo/state/published JSON carry persona names only;
  real names + private header come from gitignored `config/private.local.json`
  or the `PRIVATE_CONFIG_JSON` Actions secret (see DECISIONS.md #5).
- **Structured output**: every run writes `docs/data/reports/YYYY-MM-DD.json`
  and rebuilds `docs/data/index.json` (dates + Cardinals W/L badges).
- **Sports facts dataset**: 5 placeholders → 135 sport-tagged entries
  (37 date-keyed + 98 general, rotation can't repeat on consecutive days).
  Skip-listed facts removed (incl. v1's Don Larsen placeholder).
- **Backfill**: `scripts/backfill.py` regenerates any date range from real
  historical sources (MW archive, Wikiquote per-date pages, ESPN season
  schedules, Wayback Machine market snapshots). 2026-05-12 → 2026-06-10
  generated; `scripts/repair_missing.py` retries rate-limited gaps.
- **Telegram delivery**: `src/delivery.py`, used automatically when
  `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` are set.
- **Static site** under `docs/` (vanilla, no build step): Today view with
  split-flap date board and swipe day navigation, Archive calendar with
  Cardinals W/L dots + full-text search + `#/day/...` permalinks (legacy
  `?date=` redirects), Stats view (Chart.js vendored: song tally, spotlight
  wheel, era histogram, sport mix; word wall, quote roster, results strip),
  reading-streak chip, PWA manifest + icons + minimal service worker,
  `robots.txt` + `noindex`.
- **GitHub Actions** `daily.yml`: dual cron (14:00/15:00 UTC) with a
  9-AM-Central guard (DST-safe), publishes data, commits, sends Telegram.

### Changed
- `pytz` and `python-dateutil` dropped; stdlib `zoneinfo` (+`tzdata`) instead.
- Song/history picks are now date-seeded rather than OS-random so a re-run
  of the same day can never announce different results (see DECISIONS.md #6).
- History section softly de-prioritizes mass-casualty events when
  alternatives exist for the date (see DECISIONS.md #9).
- Home games render as `vs. Opponent` (was bare opponent name).

## v1 — Session 1 (prior)
Initial scaffold: section modules, offline-testable sections, placeholder
facts. Live-API sections coded but untested (several breakages listed above).
