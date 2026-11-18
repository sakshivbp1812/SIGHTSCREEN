"""In-process observability: request latency percentiles, error rate and LLM counters."""
import time
from collections import deque

START = time.time()
_lat: deque = deque(maxlen=500)
COUNT = {"requests": 0, "errors": 0}


def record(status: int, ms: float) -> None:
    COUNT["requests"] += 1
    COUNT["errors"] += status >= 500
    _lat.append(ms)


def summary(llm_stats: dict, provider: str) -> dict:
    s = sorted(_lat)
    pct = lambda q: round(s[min(len(s) - 1, int(q * len(s)))], 1) if s else 0
    n = COUNT["requests"]
    decided = llm_stats["accepted"] + llm_stats["rejected"]
    return {"uptime_s": int(time.time() - START), "requests": n, "error_rate_pct": round(100 * COUNT["errors"] / n, 2) if n else 0,
            "p50_ms": pct(0.5), "p95_ms": pct(0.95), "ai_provider": provider, "llm": llm_stats,
            "guard_block_rate_pct": round(100 * llm_stats["rejected"] / decided, 1) if decided else 0}
