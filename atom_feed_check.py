#!/usr/bin/env python3
import feedparser
import os
import time
import hashlib
import json
import sys

CONFIG_FILE = "/etc/check_mk/atom_feeds.json"
STATE_DIR = "/var/lib/check_mk_agent/atom_feed_states"
TTL = 3600  # Optional: auto-clear alerts after 1 hour

os.makedirs(STATE_DIR, exist_ok=True)

def sanitize_name(name):
    return "".join(c if c.isalnum() else "_" for c in name)

def load_feeds():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"<<<local:sep(0)>>>\n2 AtomFeed_Global - Failed to read config: {e}")
        sys.exit(1)

def load_state(feed_id):
    path = os.path.join(STATE_DIR, f"{feed_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_state(feed_id, data):
    path = os.path.join(STATE_DIR, f"{feed_id}.json")
    with open(path, "w") as f:
        json.dump(data, f)

def check_feed(feed_name, feed_url):
    feed_id = sanitize_name(feed_name)
    state = load_state(feed_id)
    now = int(time.time())

    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            return (3, feed_name, "Failed to parse or empty Atom feed")
    except Exception as e:
        return (3, feed_name, f"Error fetching feed: {e}")

    latest = feed.entries[0]
    entry_id = latest.get("id", "")
    entry_updated = latest.get("updated", "")
    entry_title = latest.get("title", "No title")
    entry_hash = hashlib.md5((entry_id + entry_updated).encode()).hexdigest()

    prev_hash = state.get("entry_hash")
    alert_state = state.get("alert_state", 0)
    alert_time = state.get("alert_time", 0)

    if prev_hash != entry_hash:
        # New or updated post
        if prev_hash and entry_id in prev_hash:
            alert_state = 1  # warning
            message = f"Atom feed post updated: {entry_title}"
        else:
            alert_state = 2  # critical
            message = f"New post in Atom feed: {entry_title}"

        state = {
            "entry_hash": entry_hash,
            "alert_state": alert_state,
            "alert_time": now,
            "message": message
        }
        save_state(feed_id, state)

    elif alert_state != 0 and (now - alert_time) > TTL:
        alert_state = 0
        message = "No changes in Atom feed (auto-clear)"
        state = {
            "entry_hash": entry_hash,
            "alert_state": 0,
            "alert_time": now,
            "message": message
        }
        save_state(feed_id, state)

    else:
        message = state.get("message", "No changes in Atom feed")

    return (alert_state, feed_name, message)

# === Output for CheckMK ===
print("<<<local:sep(0)>>>")

feeds = load_feeds()
for feed in feeds:
    state, name, msg = check_feed(feed["name"], feed["url"])
    print(f"{state} {name} - {msg}")
