# The Gateway Almanac

A small, fully deterministic daily almanac: a Python pipeline pulls verified
facts from public sources every morning, publishes a structured JSON snapshot
to a static site, and delivers a plain-text digest to a private chat.

No AI generates facts at runtime. Every section is API- or archive-backed:

| Section | Source |
|---|---|
| 📖 Word of the Day | Merriam-Webster per-date archive pages (RSS fallback) |
| 🏆 Sports Fact | Curated local JSON (135 reviewed entries, sport-tagged) |
| 🦁 St. Louis Sports | ESPN public JSON APIs — in-season teams only, never fabricated details |
| 📰 Market headline | WSJ/CNBC/MarketWatch RSS chain (Wayback Machine for backfill) |
| 💬 Quote of the Day | Wikiquote per-date QOTD pages via MediaWiki API |
| 📜 This Day in History | Wikipedia "On This Day" API |
| ⭐ Spotlight / 🎵 Song | Deterministic weekly/daily picks from a persona roster |

## Layout

```
src/                 pipeline (one module per section + report/publish/delivery)
scripts/             backfill.py (historical days), repair_missing.py
config/              personas.json (public) · private.local.json (gitignored)
docs/                the static site — GitHub Pages serves this directory
docs/data/reports/   one JSON per day (personas only, no private names)
.github/workflows/   daily.yml — 8 AM Central, DST-safe, commits data + sends Telegram
state.json           weekly spotlight persistence (persona name only)
```

## Run locally

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python src\main.py              # today: print + publish JSON
venv\Scripts\python src\main.py --date 2026-05-20   # regenerate a past day
venv\Scripts\python scripts\backfill.py 2026-05-12 2026-06-10
python -m http.server 4173 --directory docs  # then open http://localhost:4173
```

On macOS/Linux swap `venv\Scripts\` for `venv/bin/`.

## Privacy model

The repo, the committed state, and all published JSON contain **persona names
only**. Real display names and the private chat header live exclusively in
`config/private.local.json` (gitignored) locally, or the `PRIVATE_CONFIG_JSON`
repository secret in Actions. Without either, everything still runs — output
just uses personas. The site sets `noindex` and robots-disallows everything.

The site's **📋 Copy for chat** button produces the message-formatted text for
any day; the optional "chat names" panel substitutes real display names from
that browser's localStorage only — never transmitted or committed.

See [SETUP.md](SETUP.md) for deployment, [DECISIONS.md](DECISIONS.md) for
architecture decisions and open questions, [CHANGELOG.md](CHANGELOG.md) for
the change history.

## Cost

$0. GitHub Actions free tier (~2 min/day), GitHub Pages, public APIs.
