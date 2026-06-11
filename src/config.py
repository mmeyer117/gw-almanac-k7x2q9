"""Configuration: public personas + optional private overlay.

Privacy model:
- The repo, committed state.json, and all published site JSON contain ONLY
  persona names and the public site name. No real names, no group name.
- Real names and the private chat header come from, in priority order:
    1. env var PRIVATE_CONFIG_JSON   (GitHub Actions secret, same JSON shape)
    2. config/private.local.json     (gitignored, local machine only)
- If neither is present, everything still works — output just uses personas.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONAS_PATH = os.path.join(ROOT, "config", "personas.json")
PRIVATE_PATH = os.path.join(ROOT, "config", "private.local.json")
STATE_PATH = os.path.join(ROOT, "state.json")
DOCS_DATA_DIR = os.path.join(ROOT, "docs", "data")
REPORTS_DIR = os.path.join(DOCS_DATA_DIR, "reports")
MESSAGES_DIR = os.path.join(ROOT, "messages")

SITE_NAME = "The Gateway Almanac"
DEFAULT_HEADER = "🗞️ THE GATEWAY ALMANAC"
CHAR_LIMIT = 2500

USER_AGENT = "GatewayAlmanac/2.0 (personal daily digest)"


def load_personas():
    with open(PERSONAS_PATH, encoding="utf-8") as f:
        return json.load(f)["personas"]


def load_private():
    raw = os.environ.get("PRIVATE_CONFIG_JSON")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    if os.path.exists(PRIVATE_PATH):
        try:
            with open(PRIVATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_header(private=None):
    private = load_private() if private is None else private
    return private.get("header", DEFAULT_HEADER)


def get_name_map(private=None):
    """persona -> display name. Identity mapping when no private config."""
    private = load_private() if private is None else private
    personas = load_personas()
    real = private.get("real_names", {})
    return {p: real.get(p, p) for p in personas}
