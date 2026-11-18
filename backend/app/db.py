import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "sightscreen.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS venues(id TEXT PRIMARY KEY, name TEXT, straight_m INT, square_m INT, note TEXT, simulated INT);
CREATE TABLE IF NOT EXISTS matches(id TEXT PRIMARY KEY, title TEXT, batting TEXT, bowling TEXT, target INT, venue_id TEXT,
  start_runs INT, start_wkts INT, start_overs INT, start_balls INT, init_json TEXT, data_mode TEXT);
CREATE TABLE IF NOT EXISTS deliveries(match_id TEXT, idx INT, over INT, ball INT, bowler TEXT, batter TEXT, runs INT,
  wicket INT, how TEXT, kind TEXT, region TEXT, video_ts INT, key INT, PRIMARY KEY(match_id, idx));
CREATE TABLE IF NOT EXISTS insight_cache(k TEXT PRIMARY KEY, text TEXT);
CREATE TABLE IF NOT EXISTS ai_traces(id INTEGER PRIMARY KEY AUTOINCREMENT, ts DATETIME DEFAULT CURRENT_TIMESTAMP, match_id TEXT, question TEXT, mode TEXT,
  provider TEXT, prompt_version TEXT, status TEXT, reason TEXT, steps TEXT, total_ms INT, llm_calls INT);
CREATE TABLE IF NOT EXISTS ask_log(id INTEGER PRIMARY KEY AUTOINCREMENT, match_id TEXT, question TEXT, lens TEXT,
  source TEXT, tools TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP);
"""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
