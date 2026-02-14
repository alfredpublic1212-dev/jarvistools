import sqlite3
import os
from datetime import datetime

DB_PATH = "wisdom_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_message(project_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO memory (project_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (project_id, role, content, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

def load_memory(project_id, limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT role, content FROM memory WHERE project_id=? ORDER BY id DESC LIMIT ?",
        (project_id, limit)
    )

    rows = c.fetchall()
    conn.close()

    rows.reverse()

    return [{"role": r[0], "content": r[1]} for r in rows]