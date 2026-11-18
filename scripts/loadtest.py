"""Tiny load test: python scripts/loadtest.py http://localhost:8000 [requests] [concurrency]. Reports throughput and latency percentiles."""
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import httpx

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
n, conc = (int(sys.argv[2]) if len(sys.argv) > 2 else 300), (int(sys.argv[3]) if len(sys.argv) > 3 else 20)
M = "demo-t20-chase"
PATHS = [f"/api/matches/{M}", f"/api/matches/{M}/stats?ball=20", f"/api/matches/{M}/lens?t=47&lens=tactical&lang=hinglish", "/health"]


local = threading.local()  # one client per thread: creating a client per request would benchmark the client, not the server


def hit(i):
    t0 = time.perf_counter()
    try:
        local.c = getattr(local, "c", None) or httpx.Client(timeout=15)
        code = local.c.get(base + PATHS[i % len(PATHS)]).status_code
    except Exception:
        code = 0
    return (time.perf_counter() - t0) * 1000, code


t0 = time.perf_counter()
with ThreadPoolExecutor(conc) as ex:
    res = list(ex.map(hit, range(n)))
wall, lat = time.perf_counter() - t0, sorted(r[0] for r in res)
print(f"{n} requests, concurrency {conc}: {n / wall:.0f} req/s, errors {sum(r[1] not in (200, 429) for r in res)}, rate-limited(429) {sum(r[1] == 429 for r in res)}, "
      f"p50 {st.median(lat):.1f} ms, p95 {lat[int(.95 * n) - 1]:.1f} ms, max {lat[-1]:.1f} ms")
