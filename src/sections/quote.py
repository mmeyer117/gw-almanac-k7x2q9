"""Quote of the Day — Wikiquote per-date subpage via the MediaWiki API.

Every day has its own page ("Wikiquote:Quote of the day/June 10, 2026") whose
wikitext is a template with explicit |quote= and |author= parameters — far more
stable than scraping the rendered main page (v1's approach, which broke), and
it works for any past date, which the backfill needs.
"""
import re

import requests

from config import USER_AGENT

API = "https://en.wikiquote.org/w/api.php"


def _clean_wikitext(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)                      # inline templates
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)   # [[target|label]] -> label
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_param(wikitext, name):
    # Match "| name = value" up to the next top-level "|param=" or the closing "}}"
    m = re.search(
        rf"\|\s*{name}\s*=\s*(.*?)(?=\n\s*\|\s*\w+\s*=|\n*\}}\}}\s*$)",
        wikitext,
        re.DOTALL,
    )
    return m.group(1) if m else None


def get_data(d):
    """Returns {text, author} or None."""
    page = f"Wikiquote:Quote of the day/{d:%B} {d.day}, {d.year}"
    try:
        resp = requests.get(
            API,
            params={"action": "parse", "page": page, "prop": "wikitext",
                    "format": "json", "formatversion": 2},
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        j = resp.json()
        if "error" in j:
            return None
        wikitext = j["parse"]["wikitext"]

        quote_raw = _extract_param(wikitext, "quote")
        author_raw = _extract_param(wikitext, "author")
        if not quote_raw:
            return None

        quote = _clean_wikitext(quote_raw)
        author = _clean_wikitext(author_raw) if author_raw else ""
        if not quote:
            return None
        return {"text": quote, "author": author}
    except Exception:
        return None


def format_text(data):
    if not data:
        return None
    quote = data["text"]
    if len(quote) > 250:
        sentences = re.split(r"(?<=[.!?])\s+", quote)
        quote = sentences[0]
        if len(quote) > 250:
            quote = quote[:240].rsplit(" ", 1)[0].rstrip(",;: ") + "..."
    author = f" — {data['author']}" if data.get("author") else ""
    return f'💬 QUOTE OF THE DAY\n"{quote}"{author}'
