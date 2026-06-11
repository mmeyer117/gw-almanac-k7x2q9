"""Re-fetch sections that came back empty during a backfill (rate-limit repair).

Scans docs/data/reports/*.json for null quote/history/market/word sections,
retries each with slow pacing, updates files in place, rebuilds the index.
Weekend-null spotlight is correct and left alone.

    python scripts/repair_missing.py
"""
import json
import os
import sys
import time
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from config import REPORTS_DIR
from publish import rebuild_index
from sections import history, market, quote, word

RETRYABLE = {
    "quote": lambda d: quote.get_data(d),
    "history": lambda d: history.get_data(d),
    "market": lambda d: market.get_data(d, live=False),
    "word": lambda d: word.get_data(d),
}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    fixed = 0
    still_missing = []
    for fn in sorted(os.listdir(REPORTS_DIR)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(REPORTS_DIR, fn)
        with open(path, encoding="utf-8") as f:
            rep = json.load(f)
        d = date.fromisoformat(rep["date"])
        changed = False
        for key, fetch in RETRYABLE.items():
            if rep["sections"].get(key) is not None:
                continue
            for attempt in range(2):
                data = fetch(d)
                if data:
                    rep["sections"][key] = data
                    changed = True
                    fixed += 1
                    print(f"{d} {key}: repaired")
                    break
                time.sleep(2.5)
            else:
                still_missing.append(f"{d} {key}")
            time.sleep(1.5)
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rep, f, indent=2, ensure_ascii=False)
                f.write("\n")

    rebuild_index()
    print(f"\nrepaired sections: {fixed}")
    if still_missing:
        print("still missing (likely genuinely unavailable):")
        for s in still_missing:
            print(f"  {s}")


if __name__ == "__main__":
    main()
