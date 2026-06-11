"""Word of the Day — Merriam-Webster.

Primary source: the per-date archive page (works for today AND any past date,
verified live 2026-06-10):
    https://www.merriam-webster.com/word-of-the-day/YYYY-MM-DD
Fallback for today's date: the WOTD RSS feed (10 most recent entries).
"""
import re

import feedparser
import requests
from bs4 import BeautifulSoup

from config import USER_AGENT

MW_FEED = "https://www.merriam-webster.com/wotd/feed/rss2"
MW_ARCHIVE = "https://www.merriam-webster.com/word-of-the-day/{date}"

POS_WORDS = (
    "noun", "verb", "adjective", "adverb", "preposition",
    "pronoun", "conjunction", "interjection",
)


def _from_archive_page(d):
    url = MW_ARCHIVE.format(date=d.isoformat())
    resp = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # <title>Word of the Day: Cordial | Merriam-Webster</title>
    title = soup.find("title")
    m = re.match(r"Word of the Day:\s*(.+?)\s*\|", title.get_text(strip=True)) if title else None
    if not m:
        return None
    word = m.group(1)

    pos = ""
    pos_el = soup.find("span", class_=re.compile(r"main-attr"))
    if pos_el:
        candidate = pos_el.get_text(strip=True).lower()
        if candidate in POS_WORDS:
            pos = candidate

    definition = ""
    container = soup.find("div", class_=re.compile(r"wod-definition-container"))
    if container:
        p = container.find("p")
        if p:
            definition = p.get_text(" ", strip=True)
    if not definition:
        return None

    return {"word": word, "part_of_speech": pos, "definition": definition, "url": url}


def _from_rss(d):
    feed = feedparser.parse(MW_FEED)
    datestr = d.isoformat()
    for entry in feed.entries:
        # Entry links look like .../word-of-the-day/foible-2026-06-10
        if not entry.get("link", "").endswith(datestr):
            continue
        word = entry.title.strip()
        soup = BeautifulSoup(entry.description, "html.parser")
        text = soup.get_text(" ", strip=True)

        pos = ""
        pos_match = re.search(r"\b(%s)\b" % "|".join(POS_WORDS), text, re.IGNORECASE)
        if pos_match:
            pos = pos_match.group(1).lower()

        # Definition: the sentence(s) after the part-of-speech token, before the example ("//")
        body = text.split("//")[0]
        if pos_match:
            body = body[pos_match.end():]
        sentences = re.split(r"(?<=[.!?])\s+", body.strip())
        definition = sentences[0].strip() if sentences and sentences[0].strip() else ""
        if not definition:
            continue
        return {"word": word, "part_of_speech": pos, "definition": definition,
                "url": entry.get("link", "")}
    return None


def get_data(d):
    """Returns {word, part_of_speech, definition, url} or None."""
    try:
        data = _from_archive_page(d)
        if data:
            return data
    except Exception:
        pass
    try:
        return _from_rss(d)
    except Exception:
        return None


def format_text(data):
    if not data:
        return None
    word = data["word"].upper()
    pos = f" ({data['part_of_speech']})" if data.get("part_of_speech") else ""
    return f"📖 WORD OF THE DAY\n{word}{pos} — {data['definition']}"
