import os
import sqlite3
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "atlas.db")


def init_db():
    """Initialize the SQLite database for Atlas commands."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at REAL
        )
    """)
    conn.commit()
    conn.close()


def add_command(prompt: str):
    """Adds a command to the queue."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO command_queue (prompt, status, created_at) VALUES (?, ?, ?)",
        (prompt, "pending", time.time()),
    )
    conn.commit()
    conn.close()


def pop_command() -> str | None:
    """Retrieves and clears the oldest pending command."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get oldest pending
    cursor.execute(
        'SELECT id, prompt FROM command_queue WHERE status = "pending" ORDER BY created_at ASC LIMIT 1'
    )
    row = cursor.fetchone()

    if row:
        cmd_id, prompt = row
        # Mark as processed (or delete) - let's mark as processed to keep history
        cursor.execute(
            'UPDATE command_queue SET status = "processed" WHERE id = ?', (cmd_id,)
        )
        conn.commit()
        conn.close()
        return prompt

    conn.close()
    return None


def clear_queue():
    """Clear all pending commands."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE command_queue SET status = "cleared" WHERE status = "pending"'
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Atlas DB initialized at: {DB_PATH}")
