import hmac
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import agent, agent2, catchup, traces, data, db, evals, ingest, points, support, llm as llm_mod, ops, lens as lens_mod, stats as stats_mod
from .model import load

app = FastAPI(title="Sightscreen API", version="7.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")],
                   allow_methods=["*"], allow_headers=["*"])
_hits: dict = defaultdict(deque)


def rate_limit(request: Request):
    """Tiny per-IP limiter (60 req/min) so a public demo cannot burn the LLM key."""
    ip, now = (request.client.host if request.client else "x"), time.time()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 60:
        raise HTTPException(429, "Too many requests - try again in a minute.")
    q.append(now)


def admin(request: Request):
    """Protects operations and evaluation endpoints when ADMIN_TOKEN is set (open in the public demo if it is not)."""
    tok = os.getenv("ADMIN_TOKEN")
    if tok and not hmac.compare_digest(request.headers.get("x-admin-token", "").encode(), tok.encode()):
        raise HTTPException(401, "Admin token required")


CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; media-src 'self' https: http: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")


@app.middleware("http")
async def timing(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    resp.headers.update({"Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "Referrer-Policy": "strict-origin-when-cross-origin",
                         "Permissions-Policy": "microphone=(self), camera=(), geolocation=()", "X-Frame-Options": "DENY"})
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/ops"):
        ops.record(resp.status_code, (time.perf_counter() - t0) * 1000)
    return resp


@app.get("/api/ops/summary", dependencies=[Depends(admin)])
def ops_summary():
    return ops.summary(llm_mod.STATS, llm_mod.provider())


@app.get("/api/ops/feed/run", dependencies=[Depends(admin), Depends(rate_limit)])
def ops_feed(inject: bool = True, match_id: str = "demo-t20-chase"):
    return ingest.run(get_match(match_id), inject)


_eval_hits: dict = defaultdict(deque)


def eval_limit(request: Request):
    """Evaluations make many LLM calls, so each IP gets 6 runs per 10 minutes."""
    ip, now = (request.client.host if request.client else "x"), time.time()
    q = _eval_hits[ip]
    while q and now - q[0] > 600:
        q.popleft()
    if len(q) >= 6:
        raise HTTPException(429, "Evaluation limit reached - try again in a few minutes.")
    q.append(now)


@app.get("/api/matches/{match_id}/eval/lens", dependencies=[Depends(admin), Depends(eval_limit)])
def eval_lens(match_id: str, lens: str = "casual", lang: str = "en", side: str = "neutral", sample: int = Query(6, ge=1, le=15)):
    return evals.lens_eval(get_match(match_id), lens, lang, side, sample)


@app.get("/api/matches/{match_id}/eval/redteam", dependencies=[Depends(admin), Depends(eval_limit)])
def eval_redteam(match_id: str, lang: str = "en", side: str = "neutral"):
    return evals.red_team(get_match(match_id), lang, side)


@app.get("/api/matches/{match_id}/support/team")
def support_team(match_id: str, correction: str = "none"):
    m = get_match(match_id)
    base = points.team_points(points.ledger(m.deliveries))
    out = {"rules": points.RULES, "base": base, "corrections": {k: {"ball": v["ball"], "title": v["title"]} for k, v in points.CORRECTIONS.items()},
           "note": "Example scoring rules for the simulated match. Not official Dream11 scoring."}
    if correction in points.CORRECTIONS:
        cur = points.team_points(points.ledger(points.corrected(m.deliveries, correction)))
        d = points.diff(base, cur, correction)
        from .llm import polish
        text, src = polish(f"notice:{correction}", "Points update for your team. " + d["draft"], d["facts"], "casual", question="Write a short, kind notification explaining why the customer's points changed.",
                           extra="Audience: a fantasy-app customer.")
        out.update({"current": cur, "diff": d, "notice": {"text": text, "source": src}})
    else:
        out["current"] = base
    return out


class SupportAsk(BaseModel):
    question: str = Field(min_length=2, max_length=300)
    correction: str = "none"
    lang: str = "en"


@app.post("/api/matches/{match_id}/support/ask", dependencies=[Depends(rate_limit)])
def support_ask(match_id: str, req: SupportAsk):
    return support.answer(get_match(match_id), req.question, req.correction, req.lang)


@app.get("/api/matches/{match_id}/support/eval", dependencies=[Depends(admin), Depends(eval_limit)])
def support_eval(match_id: str):
    return support.eval_tickets(get_match(match_id))


@app.get("/api/matches/{match_id}/catchup", dependencies=[Depends(rate_limit)])
def catch_up(match_id: str, ball: int = Query(ge=0, le=200), since: int = Query(-1, ge=-1, le=200), mode: str = "quick", lang: str = "en", side: str = "neutral"):
    return catchup.build(get_match(match_id), ball, since, mode, lang, side)


@app.get("/api/matches/{match_id}/catchup/push")
def catch_up_push(match_id: str, ball: int = Query(ge=0, le=200), lang: str = "en"):
    return catchup.push(get_match(match_id), ball, lang)


@app.get("/api/matches/{match_id}/eval/briefing", dependencies=[Depends(admin), Depends(eval_limit)])
def eval_briefing(match_id: str):
    return catchup.sweep(get_match(match_id))


@app.get("/api/ops/auth")
def ops_auth(request: Request):
    tok = os.getenv("ADMIN_TOKEN")
    return {"protected": bool(tok), "ok": (not tok) or hmac.compare_digest(request.headers.get("x-admin-token", "").encode(), tok.encode())}


@app.get("/api/ops/traces", dependencies=[Depends(admin)])
def ops_traces(limit: int = Query(30, ge=1, le=100)):
    return traces.recent(limit)


@app.get("/api/ops/trace-stats", dependencies=[Depends(admin)])
def ops_trace_stats():
    return traces.stats()


@app.get("/api/matches/{match_id}/eval/agent", dependencies=[Depends(admin), Depends(eval_limit)])
def eval_agent(match_id: str):
    return evals.agent_golden(get_match(match_id))


@app.on_event("startup")
def _startup():
    data.seed()


def get_match(match_id: str):
    try:
        return load(match_id)
    except KeyError:
        raise HTTPException(404, "Unknown match")


class Scenario(BaseModel):
    ball: int = Field(ge=0, le=200)
    balls: list[tuple[int, bool]] = Field(min_length=1, max_length=6, description="[runs, wicket] per delivery")


class Ask(BaseModel):
    question: str = Field(min_length=2, max_length=300)
    lens: str = "casual"
    lang: str = "en"
    side: str = "neutral"
    ball: int = Field(ge=0, le=200, default=0)


@app.get("/health")
def health():
    from .llm import provider
    return {"status": "ok", "ai_provider": provider()}


@app.get("/api/matches/{match_id}/stats")
def stats(match_id: str, ball: int = Query(ge=0, le=200)):
    m = get_match(match_id)
    return stats_mod.compute(m, min(ball, len(m.deliveries)))


@app.get("/api/matches/{match_id}")
def match(match_id: str):
    m = get_match(match_id)
    return {"meta": {k: m.meta[k] for k in ("id", "title", "batting", "bowling", "target", "data_mode")},
            "venue": m.venue, "deliveries": [{**d, "label": m.label(d)} for d in m.deliveries],
            "frames": [f.public() for f in m.frames], "key_moments": m.key_indices(),
            "duration": m.deliveries[-1]["video_ts"] + lens_mod.WINDOW_S}


@app.get("/api/matches/{match_id}/lens", dependencies=[Depends(rate_limit)])
def lens(match_id: str, t: float = Query(ge=0, le=36000), lens: str = "casual", lang: str = "en", side: str = "neutral"):
    return lens_mod.at_time(get_match(match_id), t, lens, lang, side)


@app.get("/api/matches/{match_id}/impact", dependencies=[Depends(rate_limit)])
def impact(match_id: str, ball: int = Query(ge=1), lens: str = "casual", lang: str = "en", side: str = "neutral"):
    m = get_match(match_id)
    if ball > len(m.deliveries):
        raise HTTPException(404, "No such delivery")
    return {**lens_mod.insight(m, ball, lens, lang, side), "before": m.frames[ball - 1].public(), "after": m.frames[ball].public(),
            "delta": lens_mod.facts_for(m, ball)["delta"]}


@app.post("/api/matches/{match_id}/scenario")
def scenario(match_id: str, req: Scenario):
    m = get_match(match_id)
    if req.ball > len(m.deliveries):
        raise HTTPException(422, "ball out of range")
    from copy import deepcopy
    from .engine import apply_delivery, state_delta
    start = m.frames[req.ball]
    h = deepcopy(start)
    for runs, w in req.balls:
        apply_delivery(h, min(6, max(0, runs)), w)
    return {"before": start.public(), "after": h.public(), "delta": state_delta(start, h),
            "note": "Hypothetical deliveries from the current playhead; the replay is not changed."}


@app.post("/api/matches/{match_id}/ask", dependencies=[Depends(rate_limit)])
def ask(match_id: str, req: Ask):
    m = get_match(match_id)
    res = agent.answer(m, req.question, req.lens, min(req.ball, len(m.deliveries)), req.lang, req.side)
    with db.conn() as c:
        c.execute("INSERT INTO ask_log(match_id,question,lens,source,tools) VALUES(?,?,?,?,?)",
                  (match_id, req.question, req.lens, res["source"], ",".join(res["tools"])))
    return res


@app.post("/api/matches/{match_id}/agent", dependencies=[Depends(rate_limit)])
def agent_run(match_id: str, req: Ask):
    m = get_match(match_id)
    res = agent2.run(m, req.question, req.lens, min(req.ball, len(m.deliveries)), req.lang, req.side)
    with db.conn() as c:
        c.execute("INSERT INTO ask_log(match_id,question,lens,source,tools) VALUES(?,?,?,?,?)", (match_id, req.question, req.lens, res["source"], ",".join(res["tools"])))
    return res


@app.get("/api/matches/{match_id}/agent/stream", dependencies=[Depends(rate_limit)])
def agent_stream(match_id: str, q: str = Query(min_length=2, max_length=300), lens: str = "casual", lang: str = "en", side: str = "neutral", ball: int = Query(0, ge=0, le=200)):
    """Server-sent events: tool steps as they run, then the verified answer streamed word by word, then a final summary."""
    m = get_match(match_id)
    sse = lambda d: f"data: {json.dumps(d, ensure_ascii=False)}\n\n"

    def gen():
        for ev in agent2.run_iter(m, q, lens, min(ball, len(m.deliveries)), lang, side):
            if ev["type"] == "final":
                for w in ev["result"]["answer"].split(" "):
                    yield sse({"type": "token", "text": w + " "})
                    time.sleep(0.012)
            yield sse(ev)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/eval/rag", dependencies=[Depends(admin)])
def eval_rag():
    from . import rag
    return rag.retrieval_eval()


STATIC = Path(os.getenv("STATIC_DIR", Path(__file__).resolve().parent.parent / "static"))
if STATIC.exists():
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="web")
