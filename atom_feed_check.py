#!/usr/bin/env python3
import feedparser
import os
import time
import hashlib
import json

FEED_URL = "https://ATOM-FEED-URL"
STATE_FILE = "/tmp/atom_feed_status.json"
TTL = 3600  # optional expiry for alerts (seconds)

feed = feedparser.parse(FEED_URL)
if not feed.entries:
    print("2 atom_feed - Atom feed fetch failed or empty")
    exit(0)

latest_entry = feed.entries[0]
entry_id = latest_entry.get("id", "")
entry_updated = latest_entry.get("updated", "")
entry_title = latest_entry.get("title", "No title")

entry_hash = hashlib.md5((entry_id + entry_updated).encode()).hexdigest()
now = int(time.time())

# Load previous state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)
else:
    state = {}

previous_hash = state.get("entry_hash")
alert_state = state.get("alert_state", 0)
alert_time = state.get("alert_time", 0)

# Detect new or updated post
if previous_hash != entry_hash:
    # Decide alert level
    if previous_hash and entry_id in previous_hash:
        alert_state = 1  # Warning (updated post)
        message = f"Atom feed post updated: {entry_title}"
    else:
        alert_state = 2  # Critical (new post)
        message = f"New post in Atom feed: {entry_title}"

    # Save new state
    state = {
        "entry_hash": entry_hash,
        "alert_state": alert_state,
        "alert_time": now,
        "message": message
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Optionally clear after TTL
elif alert_state != 0 and (now - alert_time) > TTL:
    alert_state = 0
    message = "No changes in Atom feed (auto-clear)"
    state = {
        "entry_hash": entry_hash,
        "alert_state": 0,
        "alert_time": now,
        "message": message
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
else:
    # Persist current alert
    message = state.get("message", "No changes in Atom feed")

print(f"{alert_state} atom_feed - {message}")
