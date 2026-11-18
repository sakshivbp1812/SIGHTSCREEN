from app import ingest, llm
from app.model import load

M = "demo-t20-chase"


def test_both_vendor_schemas_normalise_to_the_same_event(client):
    d = load(M).deliveries[4]                      # ball 14.5, a wicket
    a, b = ingest.normalise("A", ingest.vendor_a(d)), ingest.normalise("B", ingest.vendor_b(d))
    assert a == b and a["ball"] == 5 and a["wicket"] and a["pos"] == 5
    assert ingest.vendor_b(d)["ballInOver"] == 4  # vendor B is 0-based: the classic integration trap


def test_bad_payloads_are_rejected_with_reason_codes(client):
    p = ingest.vendor_a(load(M).deliveries[0])
    for key, val, reason in (("r", "9", "runs_out_of_range"), ("bat", None, "missing_field:bat"), ("ov", "14.9", "ball_out_of_range")):
        bad = {**p, key: val}
        try:
            ingest.normalise("A", bad)
            assert False, reason
        except ValueError as e:
            assert str(e) == reason
    try:
        ingest.normalise("C", p)
    except ValueError as e:
        assert str(e) == "unknown_vendor"


def test_messy_feed_is_repaired_and_reconciles(client):
    r = client.get("/api/ops/feed/run").json()
    assert r["raw_count"] == 37 and r["duplicates"] == 1 and r["reordered"] == 1 and r["quarantined"] == 2 and r["backfilled"] == 2
    assert r["reconciled"] is True and r["final"] == r["reference"] == {"runs": 183, "wickets": 7, "overs": "20.0"}
    assert {c["status"] for c in r["cells"]} == {"ok", "dup", "reordered", "backfilled"} and len(r["cells"]) == 36
    assert "reconciled yes" in r["summary"]["text"] and {i["reason"] for i in r["incidents"] if i["type"] == "quarantined"} == {"runs_out_of_range", "missing_field:bat"}


def test_clean_feed_has_no_incidents(client):
    r = client.get("/api/ops/feed/run", params={"inject": "false"}).json()
    assert r["incidents"] == [] and r["backfilled"] == 0 and r["reconciled"] is True and r["raw_count"] == 36


def test_ops_summary_tracks_latency_and_ai_guard(client, monkeypatch):
    for _ in range(5):
        client.get(f"/api/matches/{M}")
    s = client.get("/api/ops/summary").json()
    assert s["requests"] >= 5 and s["p95_ms"] >= s["p50_ms"] >= 0 and s["error_rate_pct"] == 0
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setattr(llm, "_call", lambda prompt: "Win chance is 97 percent.")
    before = llm.STATS["rejected"]
    client.get(f"/api/matches/{M}/lens", params={"t": load(M).deliveries[4]["video_ts"] + 1})
    assert llm.STATS["rejected"] == before + 1
