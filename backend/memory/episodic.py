import sqlite3
import json
import time
import os
from typing import List, Dict, Any, Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "episodic.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            task TEXT NOT NULL,
            subtasks TEXT,
            tools_used TEXT,
            final_answer TEXT,
            confidence REAL,
            duration REAL,
            timestamp REAL,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            run_id INTEGER,
            tool_name TEXT NOT NULL,
            tool_input TEXT,
            tool_output TEXT,
            success INTEGER,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()


def save_agent_run(
    session_id: str,
    task: str,
    subtasks: List[str],
    tools_used: List[str],
    final_answer: str,
    confidence: float,
    duration: float,
    status: str = "completed"
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agent_runs 
        (session_id, task, subtasks, tools_used, final_answer, confidence, duration, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        task,
        json.dumps(subtasks),
        json.dumps(tools_used),
        final_answer,
        confidence,
        duration,
        time.time(),
        status
    ))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def save_tool_call(
    session_id: str,
    run_id: Optional[int],
    tool_name: str,
    tool_input: str,
    tool_output: str,
    success: bool
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tool_calls
        (session_id, run_id, tool_name, tool_input, tool_output, success, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        run_id,
        tool_name,
        str(tool_input)[:500],
        str(tool_output)[:1000],
        1 if success else 0,
        time.time()
    ))
    conn.commit()
    conn.close()


def get_recent_runs(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM agent_runs
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item["subtasks"] = json.loads(item["subtasks"] or "[]")
        item["tools_used"] = json.loads(item["tools_used"] or "[]")
        result.append(item)
    return result


def get_all_runs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM agent_runs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item["subtasks"] = json.loads(item["subtasks"] or "[]")
        item["tools_used"] = json.loads(item["tools_used"] or "[]")
        result.append(item)
    return result


# Initialize DB when module is imported
init_db()