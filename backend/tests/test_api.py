from app import agent, llm
from app.model import load

M = "demo-t20-chase"


def test_replay_is_a_last_ball_thriller(client):
    d = client.get(f"/api/matches/{M}").json()
    assert len(d["deliveries"]) == 36 and d["meta"]["data_mode"] == "SIMULATED DEMO"
    last = d["frames"][-1]
    assert last["result"] == "Mumbai Meteors win" and last["runs"] == 183 and last["wickets"] == 7
    assert d["frames"][-2]["result"] is None and (last["overs"], last["balls"]) == (20, 0)


def test_lens_fires_only_on_key_moments_inside_window(client):
    wicket_ts = load(M).deliveries[4]["video_ts"]            # 14.5 is the first wicket
    hit = client.get(f"/api/matches/{M}/lens", params={"t": wicket_ts + 1}).json()
    assert hit["triggerAlert"] and hit["kind"] == "WICKET" and "caught at long-on" in hit["text"]
    assert not client.get(f"/api/matches/{M}/lens", params={"t": wicket_ts + 30}).json().get("kind") == "WICKET"
    quiet = client.get(f"/api/matches/{M}/lens", params={"t": load(M).deliveries[2]["video_ts"] + 1}).json()
    assert quiet["triggerAlert"] is False                     # a dot ball is not a key moment
    assert client.get(f"/api/matches/{M}/lens", params={"t": 0}).json()["triggerAlert"] is False


def test_lens_variants_differ_but_share_facts(client):
    t = load(M).deliveries[4]["video_ts"] + 1
    r = {l: client.get(f"/api/matches/{M}/lens", params={"t": t, "lens": l}).json() for l in ("casual", "tactical", "fantasy")}
    assert len({v["text"] for v in r.values()}) == 3
    assert all("4 down" in v["text"] for v in r.values())


def test_scenario_does_not_mutate_replay(client):
    r = client.post(f"/api/matches/{M}/scenario", json={"ball": 10, "balls": [[6, False], [0, True]]}).json()
    assert r["delta"]["runs_added"] == 6 and r["delta"]["wickets_lost"] == 1 and r["delta"]["balls_used"] == 2
    assert client.get(f"/api/matches/{M}").json()["frames"][10] == r["before"]


def test_ask_is_grounded_and_reports_tools(client):
    r = client.post(f"/api/matches/{M}/ask", json={"question": "What is the required rate?", "ball": 10}).json()
    assert "match_state" in r["tools"] and "rules engine" in r["source"]
    f = load(M).frames[10]
    assert f"{f.required_rate:.2f}" in r["answer"]


def test_agent_guardrails(client):
    bets = client.post(f"/api/matches/{M}/ask", json={"question": "Give me betting odds"}).json()
    assert bets["source"] == "policy guardrail"
    cap = client.post(f"/api/matches/{M}/ask", json={"question": "Who should I captain?", "ball": 20}).json()
    assert "fantasy_watchlist" in cap["tools"] and "not official Dream11 points" in cap["answer"]
    prob = client.post(f"/api/matches/{M}/ask", json={"question": "What is their win probability?", "ball": 5}).json()
    assert "honesty_check" in prob["tools"]
    rule = client.post(f"/api/matches/{M}/ask", json={"question": "Explain Umpire's Call"}).json()
    assert "rules_search" in rule["tools"] and rule["citations"][0]["id"] == "R-umpires-call" and "clipping" in rule["answer"]


def test_stats_are_consistent_with_the_engine(client):
    s = client.get(f"/api/matches/{M}/stats", params={"ball": 36}).json()
    assert sum(o["runs"] for o in s["runs_by_over"]) == 71 and sum(w["wickets"] for w in s["bowlers"]) == 4
    assert len(s["runs_by_over"]) == 6 and s["watchlist"][0]["impact"] >= s["watchlist"][-1]["impact"]
    assert sum(s["boundaries"].values()) == sum(b["fours"] + b["sixes"] for b in s["batters"])


def test_provider_selection_and_ai_path(client, monkeypatch):
    assert llm.provider() == "none"
    monkeypatch.setenv("GROQ_API_KEY", "x")
    assert llm.provider() == "groq"
    monkeypatch.setenv("GEMINI_API_KEY", "y"); monkeypatch.setenv("AI_PROVIDER", "gemini")
    assert llm.provider() == "gemini"
    monkeypatch.setattr(llm, "_call", lambda prompt: "Dev Malhotra is out and 4 down, a big swing.")
    t = load(M).deliveries[4]["video_ts"] + 1
    ok = client.get(f"/api/matches/{M}/lens", params={"t": t, "lens": "fantasy"}).json()
    assert ok["source"].startswith("AI") and "big swing" in ok["text"]
    monkeypatch.setattr(llm, "_call", lambda prompt: "Win chance is 97 percent.")
    bad = client.get(f"/api/matches/{M}/lens", params={"t": t, "lens": "tactical"}).json()
    assert "rejected" in bad["source"] and "97" not in bad["text"]


def test_llm_guard_rejects_invented_numbers():
    facts = "Need 25 from 18 balls, required rate 8.33."
    assert llm.grounded("Need 25 from 18 balls.", facts)
    assert not llm.grounded("Need 25 from 18 balls, win chance 73%.", facts)


def test_unknown_match_and_bad_input(client):
    assert client.get("/api/matches/nope").status_code == 404
    assert client.post(f"/api/matches/{M}/scenario", json={"ball": 1, "balls": []}).status_code == 422
    assert client.get("/health").json()["status"] == "ok"
