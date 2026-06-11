"""What's Moving the Market — top business headline from RSS.

Live: feed chain (all verified alive 2026-06-10).
Backfill: the same WSJ Markets feed via the Wayback Machine, which captures it
near-daily — so even backdated reports carry the real headline of that day.
A snapshot is only accepted if it was captured on the report date or the day
before (a morning report naturally reflects the prior evening's news); days
with no acceptable snapshot just omit the section.
"""
import re

import feedparser
import requests

from config import USER_AGENT

FEEDS = [
    ("WSJ Markets", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"),
    ("CNBC Markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
]

WAYBACK_FEED = FEEDS[0][1]  # WSJ Markets — densest Wayback capture history
WAYBACK_AVAILABLE = "https://archive.org/wayback/available"


def _entry_to_data(entry, source):
    title = entry.title.strip()
    summary = ""
    if entry.get("summary"):
        summary = re.sub(r"<[^>]+>", "", entry.summary).strip()
        sentences = re.split(r"(?<=[.!?])\s+", summary)
        summary = " ".join(sentences[:2])
        if len(summary) > 280:
            summary = summary[:270].rstrip() + "..."
    if summary.lower() == title.lower():
        summary = ""
    return {"headline": title, "summary": summary, "source": source}


def get_data_live():
    for source, feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                return _entry_to_data(feed.entries[0], source)
        except Exception:
            continue
    return None


def get_data_archived(d):
    """Real headline for a past date via Wayback Machine, or None."""
    try:
        resp = requests.get(
            WAYBACK_AVAILABLE,
            params={"url": WAYBACK_FEED, "timestamp": f"{d:%Y%m%d}1300"},
            timeout=25, headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        snap = resp.json().get("archived_snapshots", {}).get("closest", {})
        url, ts = snap.get("url"), snap.get("timestamp", "")
        if not url or not ts:
            return None
        snap_date = ts[:8]
        accepted = {f"{d:%Y%m%d}"}
        from datetime import timedelta
        accepted.add(f"{d - timedelta(days=1):%Y%m%d}")
        if snap_date not in accepted:
            return None
        # 'id_' suffix on the timestamp serves the raw original bytes
        raw_url = re.sub(r"(/web/\d+)/", r"\1id_/", url)
        raw = requests.get(raw_url, timeout=30, headers={"User-Agent": USER_AGENT})
        raw.raise_for_status()
        feed = feedparser.parse(raw.content)
        if feed.entries:
            return _entry_to_data(feed.entries[0], "WSJ Markets")
    except Exception:
        pass
    return None


def get_data(d, live=True):
    return get_data_live() if live else get_data_archived(d)


def format_text(data):
    if not data:
        return None
    headline = data["headline"].rstrip(".")
    if data.get("summary"):
        return f"📰 WHAT'S MOVING THE MARKET\n{headline}. {data['summary']}"
    return f"📰 WHAT'S MOVING THE MARKET\n{headline}."
