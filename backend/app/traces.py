"""AI observability: every agent run is stored with per-step latency and a machine-readable outcome."""
import json
from . import db


def record(match_id: str, question: str, result: dict, status: str, reason: str, provider: str) -> None:
    try:
        with db.conn() as c:
            c.execute("INSERT INTO ai_traces(match_id,question,mode,provider,prompt_version,status,reason,steps,total_ms,llm_calls) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (match_id, question[:300], result.get("mode"), provider, result.get("prompt_version"), status, reason,
                       json.dumps(result.get("trace", [])), result.get("total_ms", 0), result.get("llm_calls", 0)))
    except Exception:
        pass  # observability must never break a fan's request


def recent(n: int = 30) -> list:
    with db.conn() as c:
        rows = c.execute("SELECT * FROM ai_traces ORDER BY id DESC LIMIT ?", (max(1, min(n, 100)),)).fetchall()
    return [{**dict(r), "steps": json.loads(r["steps"] or "[]")} for r in rows]


def stats(n: int = 200) -> dict:
    with db.conn() as c:
        rows = c.execute("SELECT mode,status,reason,total_ms,llm_calls,steps FROM ai_traces ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    total = len(rows)
    lat = sorted(r["total_ms"] or 0 for r in rows)
    pct = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))] if lat else 0
    reasons: dict = {}
    for r in rows:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    agent = [r for r in rows if r["mode"] == "agent"]
    return {"runs": total, "agent_answered": len(agent), "agent_pct": round(100 * len(agent) / total) if total else 0,
            "fallbacks": sum(r["status"] == "fallback" for r in rows), "p50_ms": pct(0.5), "p95_ms": pct(0.95),
            "avg_steps": round(sum(len(json.loads(r["steps"] or "[]")) for r in rows) / total, 2) if total else 0,
            "llm_calls": sum(r["llm_calls"] or 0 for r in rows), "reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1]))}
