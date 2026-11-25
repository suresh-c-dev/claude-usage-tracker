import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

# The database file sits in the same folder as this script
DB_PATH = Path(__file__).parent / "usage.db"
WINDOW = timedelta(hours=5)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_at TEXT NOT NULL,
            kind TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hit_at TEXT NOT NULL,
            total INTEGER NOT NULL
        )
    """)
    return conn


def log_message(kind):
    now = datetime.now().isoformat(timespec="seconds")
    conn = connect()
    with conn:  # saves (commits) automatically
        conn.execute(
            "INSERT INTO messages (sent_at, kind) VALUES (?, ?)",
            (now, kind),
        )
    conn.close()
    print(f"Saved {kind} message at {now}")


def current_window():
    """Return (start, counts) for the active window, or (None, None)."""
    conn = connect()
    rows = conn.execute(
        "SELECT sent_at, kind FROM messages ORDER BY sent_at"
    ).fetchall()
    conn.close()

    start = None
    counts = {"short": 0, "long": 0, "file": 0}

    for sent_at, kind in rows:
        sent = datetime.fromisoformat(sent_at)
        # A new window starts at the first message after the old one ends
        if start is None or sent >= start + WINDOW:
            start = sent
            counts = {"short": 0, "long": 0, "file": 0}
        counts[kind] += 1

    if start is None or datetime.now() >= start + WINDOW:
        return None, None
    return start, counts


def show_status():
    start, counts = current_window()
    if start is None:
        print("No active window. It starts with your next message.")
        return

    reset_at = start + WINDOW
    seconds_left = int((reset_at - datetime.now()).total_seconds())
    hours, remainder = divmod(seconds_left, 3600)
    minutes = remainder // 60

    print(f"Messages in this window: {sum(counts.values())}")
    for kind, number in counts.items():
        print(f"  {kind}: {number}")
    print(f"Resets at {reset_at:%I:%M %p} ({hours}h {minutes}m left)")


def record_limit():
    start, counts = current_window()
    if start is None:
        print("No active window, so nothing to record. Log your messages first.")
        return

    total = sum(counts.values())
    now = datetime.now().isoformat(timespec="seconds")
    conn = connect()
    with conn:
        conn.execute(
            "INSERT INTO blocks (hit_at, total) VALUES (?, ?)",
            (now, total),
        )
    conn.close()
    print(f"Recorded: blocked after {total} messages")


def show_history():
    conn = connect()
    rows = conn.execute(
        "SELECT hit_at, total FROM blocks ORDER BY hit_at"
    ).fetchall()
    conn.close()

    if not rows:
        print("No blocks recorded yet.")
        return

    for hit_at, total in rows:
        hit = datetime.fromisoformat(hit_at)
        print(f"{hit:%d %b %I:%M %p} - blocked after {total} messages")

    typical = median(total for _, total in rows)
    print(f"Typical cap: about {typical:g} messages (from {len(rows)} blocks)")


def main():
    parser = argparse.ArgumentParser(description="Claude free plan usage tracker")
    commands = parser.add_subparsers(dest="command", required=True)

    log = commands.add_parser("log", help="record a message you sent")
    log.add_argument("kind", choices=["short", "long", "file"])

    commands.add_parser("status", help="show count and reset time")
    commands.add_parser("limit", help="record that Claude blocked you")
    commands.add_parser("history", help="show past blocks and typical cap")

    args = parser.parse_args()

    if args.command == "log":
        log_message(args.kind)
    elif args.command == "status":
        show_status()
    elif args.command == "limit":
        record_limit()
    elif args.command == "history":
        show_history()


if __name__ == "__main__":
    main()