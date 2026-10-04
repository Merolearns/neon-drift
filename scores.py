"""SQLite high-score table. Top 10, name + score + wave reached."""

import sqlite3

import config


class ScoreDB:
    def __init__(self, path=None):
        self.path = path or config.db_path()
        self._init()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._connect() as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS scores (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       score INTEGER NOT NULL,
                       wave INTEGER NOT NULL,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )"""
            )

    def add_score(self, name, score, wave):
        name = (name or "ACE").strip()[: config.MAX_NAME_LEN] or "ACE"
        with self._connect() as con:
            con.execute(
                "INSERT INTO scores (name, score, wave) VALUES (?, ?, ?)",
                (name.upper(), int(score), int(wave)),
            )

    def top(self, limit=config.SCORE_TABLE_SIZE):
        with self._connect() as con:
            rows = con.execute(
                "SELECT name, score, wave FROM scores "
                "ORDER BY score DESC, created_at ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return rows

    def qualifies(self, score):
        """True if the score makes the table (or the table isn't full)."""
        rows = self.top()
        return len(rows) < config.SCORE_TABLE_SIZE or score > rows[-1][1]

    def best(self):
        rows = self.top(1)
        return rows[0][1] if rows else 0
