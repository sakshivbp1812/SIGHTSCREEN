from app import points, support
from app.model import load

M = "demo-t20-chase"


def pts(ds):
    return points.team_points(points.ledger(ds))


def test_points_match_hand_calculation(client):
    t = pts(load(M).deliveries)
    by = {p["name"]: p for p in t["players"]}
    assert by["Rohan Pillai"]["base"] == 27        # dot 14.3 + wicket 14.5 (25) + dot 18.3
    assert by["Dev Malhotra"]["base"] == 1         # one run at 14.1, dismissed 14.5 for 0
    assert by["Kabir Sethi"]["points"] == by["Kabir Sethi"]["base"] * 2 and by["Arjun Rane"]["points"] == by["Arjun Rane"]["base"] * 1.5
    assert t["total"] == 149.5 and len(points.ledger(load(M).deliveries)) > 30


def test_corrections_change_the_right_players_only(client):
    ds, base = load(M).deliveries, pts(load(M).deliveries)
    c1 = points.diff(base, pts(points.corrected(ds, "c1")), "c1")
    assert [(d["name"], d["delta"]) for d in c1["deltas"]] == [("Rohan Pillai", -25)] and c1["after"] == 124.5
    c2 = points.diff(base, pts(points.corrected(ds, "c2")), "c2")
    assert [(d["name"], d["delta"], d["base_delta"]) for d in c2["deltas"]] == [("Kabir Sethi", -10.0, -5)]   # captain doubles a -5 change
    assert load(M).deliveries[4]["how"] == "caught at long-on"                                              # original data untouched


def test_copilot_explains_change_with_exact_numbers(client):
    r = support.answer(load(M), "Why did my points drop after the match?", "c1", use_ai=False)
    assert r["resolved"] and "Rohan Pillai" in r["answer"] and "-25" in r["answer"] and "124.5" in r["answer"] and "correction_log" in r["tools"]
    none = support.answer(load(M), "Why did my points change?", "none", use_ai=False)
    assert none["resolved"] and "No scoring corrections" in none["answer"]


def test_copilot_never_answers_out_of_scope(client):
    for q in ("Where is my withdrawal?", "My KYC was rejected", "What is my rank in the contest?", "Guarantee I win"):
        r = support.answer(load(M), q, "c1", use_ai=False)
        assert not r["resolved"] and r["handoff"]["queue"] and "Outside match-points data" in r["handoff"]["summary"]
    assert support.answer(load(M), "Refund my entry fee", "none", use_ai=False)["handoff"]["queue"] == "Payments"


def test_deflection_eval_is_safe(client):
    e = client.get(f"/api/matches/{M}/support/eval").json()
    assert e["routing_correct_pct"] == 100 and e["false_resolutions"] == 0 and e["key_facts_pct"] == 100 and e["auto_resolved_pct"] == 57


def test_support_api_and_notice(client):
    t = client.get(f"/api/matches/{M}/support/team", params={"correction": "c1"}).json()
    assert t["base"]["total"] == 149.5 and t["current"]["total"] == 124.5 and "25" in t["notice"]["text"]
    a = client.post(f"/api/matches/{M}/support/ask", json={"question": "Mere points kam kyun hue?", "correction": "c1"}).json()
    assert a["resolved"] and "Rohan Pillai" in a["answer"]
