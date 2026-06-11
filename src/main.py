"""Daily report CLI.

    python src/main.py                     today: print + publish JSON (+ Telegram if configured)
    python src/main.py --date 2026-06-01   regenerate a specific day (archived sources)
    python src/main.py --no-publish        print only, write nothing
    python src/main.py --no-telegram       skip delivery even if configured
"""
import argparse
import os
import sys
from datetime import date

# Make sibling modules importable regardless of invocation directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import report as report_mod
from datefmt import now_ct
from delivery import send_telegram, telegram_configured
from publish import rebuild_index, write_report_json


def main():
    # Windows consoles default to cp1252, which can't print emoji
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Generate the daily report")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today in CT)")
    parser.add_argument("--no-publish", action="store_true", help="don't write JSON/index")
    parser.add_argument("--no-telegram", action="store_true", help="don't send to Telegram")
    args = parser.parse_args()

    today_ct = now_ct().date()
    report_date = date.fromisoformat(args.date) if args.date else today_ct
    live = report_date == today_ct

    rep = report_mod.build(report_date, live=live)

    private = config.load_private()
    text = report_mod.render_text(rep, config.get_header(private), config.get_name_map(private))

    print(text)
    warning = report_mod.length_warning(text)
    if warning:
        print(warning, file=sys.stderr)

    empty = [k for k, v in rep["sections"].items() if v is None]
    if empty:
        print(f"(sections omitted: {', '.join(empty)})", file=sys.stderr)

    if not args.no_publish:
        path = write_report_json(rep)
        rebuild_index()
        print(f"published {os.path.relpath(path, config.ROOT)}", file=sys.stderr)

        os.makedirs(config.MESSAGES_DIR, exist_ok=True)
        msg_path = os.path.join(config.MESSAGES_DIR, "today.txt")
        with open(msg_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")

    if live and not args.no_telegram and telegram_configured():
        ok = send_telegram(text)
        print("telegram: sent" if ok else "telegram: FAILED", file=sys.stderr)


if __name__ == "__main__":
    main()
