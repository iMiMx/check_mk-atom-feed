Ensure the script runs on the host where the CheckMK agent is installed. If it's not the CheckMK server itself, it must be deployed on the target agent host (could be the same).

Path: /usr/lib/check_mk_agent/local/atom_feed_check.py
Permissions: Must be executable by the agent user.

New post: Critical alert (state 2), persists across checks.
Updated post: Warning alert (state 1), persists.
No change: Keeps prior alert unless it’s explicitly cleared.
Optional TTL logic: Clears alerts after 1 hour (adjust TTL or remove it).
