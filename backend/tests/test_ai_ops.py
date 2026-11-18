import json
from app import agent2, evals, llm, traces
from app.model import load

M = "demo-t20-chase"


def script(monkeypatch, replies):
    it = iter(replies)
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setattr(llm, "_call", lambda prompt, system=None: next(it, "not json"))


def j(**k):
    return json.dumps(k)


def test_every_agent_run_leaves_a_trace_with_step_latency(client, monkeypatch):
    m = load(M)
    s = m.frames[20]
    script(monkeypatch, [j(tool="get_state", args={}), j(final=f"Need {s.runs_needed} from {s.balls_remaining}.", citations=[])])
    agent2.run(m, "Where are we?", "casual", 20)
    script(monkeypatch, [j(tool="get_state", args={}), j(final="A 92 percent chance.", citations=[])])
    agent2.run(m, "Who wins?", "casual", 20)
    agent2.run(m, "Give me betting odds", "casual", 20)
    st = traces.stats()
    assert st["runs"] == 3 and st["agent_answered"] == 1 and st["fallbacks"] == 1 and st["llm_calls"] == 4
    assert st["reasons"] == {"ok": 1, "verification_failed:number_not_in_tools": 1, "policy_refusal": 1}
    first = traces.recent(5)[-1]
    assert first["status"] == "accepted" and first["prompt_version"] == agent2.PROMPT_VERSION and first["provider"] == "groq"
    assert [s["tool"] for s in first["steps"]] == ["get_state"] and first["steps"][0]["llm_ms"] >= 0 and first["steps"][0]["tool_ms"] >= 0


def test_trace_endpoints(client, monkeypatch):
    script(monkeypatch, [])
    client.post(f"/api/matches/{M}/agent", json={"question": "Explain the free hit", "ball": 5})
    assert client.get("/api/ops/trace-stats").json()["runs"] == 1
    t = client.get("/api/ops/traces", params={"limit": 5}).json()
    assert len(t) == 1 and t[0]["question"] == "Explain the free hit" and t[0]["status"] == "fallback"


def test_golden_regression_passes_without_calling_a_model(client, monkeypatch):
    monkeypatch.setattr(llm, "_call", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no real model call allowed")))
    r = client.get(f"/api/matches/{M}/eval/agent").json()
    assert r["total"] == r["passed"] == 10 and r["model"].startswith("scripted") and all(c["passed"] for c in r["cases"])
    assert traces.stats()["runs"] == 0                                                                       # offline runs are not stored


def test_a_broken_trace_store_never_breaks_the_answer(client, monkeypatch):
    m = load(M)

    def boom():
        raise RuntimeError("db down")
    monkeypatch.setattr(traces.db, "conn", boom)
    r = agent2.run(m, "What is the required rate?", "casual", 10)
    assert r["mode"] == "router" and "required" in r["answer"].lower()


def test_admin_token_protects_operations_but_not_fans(client, monkeypatch):
    protected = ["/api/ops/summary", "/api/ops/feed/run", "/api/ops/traces", "/api/ops/trace-stats", "/api/eval/rag", f"/api/matches/{M}/eval/lens",
                 f"/api/matches/{M}/eval/redteam", f"/api/matches/{M}/eval/briefing", f"/api/matches/{M}/eval/agent", f"/api/matches/{M}/support/eval"]
    from app import main
    ok = lambda hdr=None: [client.get(p, headers=hdr).status_code for p in protected]
    assert ok() == [200] * len(protected)                                                                    # open when no token is configured
    main._eval_hits.clear()
    assert client.get("/api/ops/auth").json() == {"protected": False, "ok": True}
    monkeypatch.setenv("ADMIN_TOKEN", "s3cret")
    assert ok() == [401] * len(protected)
    assert ok({"X-Admin-Token": "wrong"}) == [401] * len(protected)
    assert ok({"X-Admin-Token": "s3cret"}) == [200] * len(protected)
    assert client.get("/api/ops/auth").json() == {"protected": True, "ok": False}
    assert client.get("/api/ops/auth", headers={"X-Admin-Token": "s3cret"}).json() == {"protected": True, "ok": True}
    for p in (f"/api/matches/{M}", f"/api/matches/{M}/lens?t=47", f"/api/matches/{M}/catchup?ball=22", "/health"):
        assert client.get(p).status_code == 200                                                              # fan-facing endpoints stay open
    assert client.post(f"/api/matches/{M}/ask", json={"question": "What is the required rate?"}).status_code == 200


def test_security_headers_are_set(client):
    h = client.get("/health").headers
    assert "default-src 'self'" in h["content-security-policy"] and "frame-ancestors 'none'" in h["content-security-policy"]
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY" and "microphone=(self)" in h["permissions-policy"]
