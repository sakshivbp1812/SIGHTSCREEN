from app import catchup, llm
from app.model import load

M = "demo-t20-chase"
URL = f"/api/matches/{M}/catchup"


def test_moments_are_the_highest_impact_ones(client):
    m = load(M)
    r = client.get(URL, params={"ball": 22, "since": 0, "mode": "quick"}).json()
    key = [d["idx"] for d in m.deliveries[:22] if d["key"]]
    expect = sorted(sorted(key, key=lambda i: (-catchup.impact(m, i), i))[:2])
    assert [x["idx"] for x in r["moments"]] == expect and r["skipped_moments"] == len(key) - 2


def test_same_numbers_in_every_language(client):
    for lang in ("en", "hinglish", "hi"):
        r = client.get(URL, params={"ball": 22, "lang": lang}).json()
        assert "26" in r["text"] and "14" in r["text"] and "11.14" in r["text"] and "Arjun Rane" in r["text"]
    assert any("\u0900" <= c <= "\u097f" for c in client.get(URL, params={"ball": 22, "lang": "hi"}).json()["text"])


def test_modes_respect_word_budgets(client):
    q = client.get(URL, params={"ball": 30, "since": 0, "mode": "quick"}).json()
    f = client.get(URL, params={"ball": 30, "since": 0, "mode": "full"}).json()
    assert q["words"] <= 90 and f["words"] <= 170 and len(f["moments"]) > len(q["moments"]) and q["read_seconds"] <= 30


def test_edges_start_end_and_nothing_new(client):
    start = client.get(URL, params={"ball": 0}).json()
    assert "70" in start["text"] and start["moments"] == []
    end = client.get(URL, params={"ball": 36, "since": 30}).json()
    assert "Mumbai Meteors win" in end["text"] and "183/7" in end["text"]
    quiet = client.get(URL, params={"ball": 3, "since": 3}).json()
    assert "Nothing major" in quiet["text"]
    assert client.get(URL, params={"ball": 300}).status_code == 422


def test_fan_side_changes_the_trend_framing(client):
    m = load(M)
    since, ball = 4, 16
    p0, p1 = m.frames[since].pressure, m.frames[ball].pressure
    assert p0 != p1
    bat = client.get(URL, params={"ball": ball, "since": since, "side": "batting"}).json()["text"]
    bowl = client.get(URL, params={"ball": ball, "since": since, "side": "bowling"}).json()["text"]
    easing = p1 < p0                                       # lower pressure is good for the chasing side
    assert (f"Big moment for {m.meta['batting']}" in bat) == easing and (f"Tough moment for {m.meta['batting']}" in bat) == (not easing)
    assert (f"Big moment for {m.meta['bowling']}" in bowl) == (not easing) and (f"Tough moment for {m.meta['bowling']}" in bowl) == easing


def test_push_payload(client):
    p = client.get(URL + "/push", params={"ball": 5}).json()
    assert p["send"] and p["priority"] == "high" and p["title"].startswith("Wicket!") and p["deep_link"] == "/?catchup=5&lang=en" and len(p["title"]) < 60
    assert client.get(URL + "/push", params={"ball": 3}).json() == {"send": False}
    assert client.get(URL + "/push", params={"ball": 5, "lang": "hi"}).json()["title"].startswith("विकेट!")


def test_sweep_is_perfect_on_the_rules_engine(client):
    s = client.get(f"/api/matches/{M}/eval/briefing").json()
    assert s["n"] == 222 and set(s["pass_pct"].values()) == {100} and s["max_words"] <= 170


def test_ai_path_is_guarded(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setattr(llm, "_call", lambda prompt: "You are 26 needed from 14 balls with Arjun Rane on strike.")
    ok = client.get(URL, params={"ball": 22}).json()
    assert ok["source"].startswith("AI") and ok["text"].startswith("You are 26")
    monkeypatch.setattr(llm, "_call", lambda prompt: "Meteors have a 91 percent chance to win.")
    bad = client.get(URL, params={"ball": 23}).json()
    assert "rejected" in bad["source"] and "91" not in bad["text"]
