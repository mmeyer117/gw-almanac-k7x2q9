# Setup — from this machine to a live site

Everything below is one-time. Total ~15 minutes.

## 0. Privacy preflight (already done, know about it)

- `config/private.local.json` is **gitignored** — it holds the real-name
  mapping and your private chat header. Never commit it.
- Git history was rebuilt before first push so no commit contains private
  names. A `local-history` branch (if present) preserves the original
  development history **locally** — never push that branch.
- Verify any time (substitute the private words you care about):
  `git grep -I -iE "<groupname>|<realname>" $(git rev-list --all) -- .`
  — should print nothing.

## 1. GitHub login + repo

```powershell
gh auth login                  # browser flow, pick HTTPS
cd <your local project folder>
gh repo create gw-almanac-k7x2q9 --public --source . --push
```

Pick your own repo name (DECISIONS.md #3 discusses obscurity). Push only
`main`.

## 2. GitHub Pages

Repo → Settings → Pages → "Deploy from a branch" → branch `main`,
folder `/docs` → Save. The site appears at
`https://<username>.github.io/<repo>/` within a couple of minutes.

## 3. Secrets (repo → Settings → Secrets and variables → Actions)

| Secret | Value |
|---|---|
| `PRIVATE_CONFIG_JSON` | the entire contents of `config/private.local.json`, as one JSON string |
| `TELEGRAM_BOT_TOKEN` | from step 4 |
| `TELEGRAM_CHAT_ID` | from step 4 |

Without the Telegram secrets the workflow still runs and publishes the site —
it just skips delivery. Without `PRIVATE_CONFIG_JSON` the Telegram text would
use persona names.

## 4. Telegram bot (5 minutes)

1. In Telegram, message **@BotFather** → `/newbot` → pick a name and a
   username. BotFather replies with the **bot token** → secret
   `TELEGRAM_BOT_TOKEN`.
2. Message your new bot once (anything) so it can reply to you.
3. Get your chat id: open
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   in a browser and read `"chat":{"id":123456789,...}` → secret
   `TELEGRAM_CHAT_ID`.
4. Each morning the bot sends you the report → long-press → copy → paste
   into iMessage.

## 5. First run

Repo → Actions → "Daily report" → **Run workflow** (manual runs bypass the
8 AM gate). Confirm: Telegram message arrives, a new commit lands with
`docs/data/reports/<today>.json`, and the site shows today.

From then on it fires at 8:00 AM Central daily (DST handled by the dual
cron + guard) — early enough to share whenever the group wakes up.

## 6. Local development

```powershell
venv\Scripts\python src\main.py --no-publish      # preview today without writing
venv\Scripts\python src\main.py                   # full local run (writes JSON + messages\today.txt)
venv\Scripts\python scripts\backfill.py 2026-05-12 2026-06-10
python -m http.server 4173 --directory docs       # local site preview
```

`messages\today.txt` (real names) is gitignored; copy from there if you ran
locally instead of waiting for Telegram.
