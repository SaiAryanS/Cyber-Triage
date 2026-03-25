import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List


class IncidentMemory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    alert_id TEXT,
                    created_at TEXT,
                    status TEXT,
                    severity TEXT,
                    confidence REAL,
                    summary TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT,
                    step_id TEXT,
                    title TEXT,
                    status TEXT,
                    details TEXT,
                    ts TEXT
                )
                """
            )

    def create_incident(self, incident_id: str, alert_id: str, summary: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents
                (incident_id, alert_id, created_at, status, severity, confidence, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (incident_id, alert_id, datetime.utcnow().isoformat(), "in_progress", "unknown", 0.0, summary),
            )

    def update_incident_outcome(self, incident_id: str, severity: str, confidence: float, status: str = "triaged") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE incidents
                SET severity = ?, confidence = ?, status = ?
                WHERE incident_id = ?
                """,
                (severity, confidence, status, incident_id),
            )

    def add_step_event(self, incident_id: str, step_id: str, title: str, status: str, details: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO incident_steps
                (incident_id, step_id, title, status, details, ts)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (incident_id, step_id, title, status, details, datetime.utcnow().isoformat()),
            )

    def get_incident_history(self, incident_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT step_id, title, status, details, ts
                FROM incident_steps
                WHERE incident_id = ?
                ORDER BY id ASC
                """,
                (incident_id,),
            )
            rows = cursor.fetchall()
        return [
            {"step_id": r[0], "title": r[1], "status": r[2], "details": r[3], "ts": r[4]}
            for r in rows
        ]
