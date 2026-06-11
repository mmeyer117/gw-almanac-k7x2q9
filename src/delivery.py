"""Telegram delivery — plain sendMessage POST.

Needs env vars TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (GitHub Secrets in
Actions). Silently unavailable when they're absent so local runs just print.
"""
import os
import sys

import requests


def telegram_configured():
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=20,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Telegram delivery failed: {e}", file=sys.stderr)
        return False
