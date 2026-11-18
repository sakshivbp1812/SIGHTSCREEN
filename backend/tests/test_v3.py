from app import agent, evals, llm
from app.model import load

M = "demo-t20-chase"
LENS = f"/api/matches/{M}/lens"


def ts(i):
    return load(M).deliveries[i]["video_ts"] + 1


def test_hinglish_and_hindi_keep_verifiable_numbers(client):
    en = client.get(LENS, params={"t": ts(4)}).json()
    hl = client.get(LENS, params={"t": ts(4), "lang": "hinglish"}).json()
    hi = client.get(LENS, params={"t": ts(4), "lang": "hi"}).json()
    assert "out ho gaye" in hl["text"] and "आउट" in hi["text"] and "लॉन्ग-ऑन पर कैच" in hi["text"]
    for r in (hl, hi):                                   # same engine numbers in every language
        assert "4" in r["text"] and "64" in r["text"] and "12.39" in r["text"] and "Dev Malhotra" in r["text"]
    assert en["text"] != hl["text"] != hi["text"]


def test_fan_perspective_flips_tone(client):
    wicket = ts(4)
    bat = client.get(LENS, params={"t": wicket, "side": "batting"}).json()["text"]
    bowl = client.get(LENS, params={"t": wicket, "side": "bowling"}).json()["text"]
    assert "Tough moment for Mumbai Meteors" in bat and "Big moment for Chennai Comets" in bowl
    six = load(M).deliveries[8]["video_ts"] + 1          # ball 15.3 is a six
    assert "Big moment for Mumbai Meteors" in client.get(LENS, params={"t": six, "side": "batting"}).json()["text"]
    assert "Moment for" not in client.get(LENS, params={"t": wicket}).json()["text"]


def test_devanagari_digits_are_checked_by_the_guard():
    assert not llm.grounded("जीतने की संभावना ९७ प्रतिशत", "Need 25 from 18 balls")
    assert llm.grounded("25 रन चाहिए 18 गेंद में", "Need 25 from 18 balls")


def test_agent_understands_hinglish_and_hindi(client):
    m = load(M)
    r = agent.answer(m, "Agar agla ball chhakka ho toh kya hoga?", "casual", 10, "hinglish")
    assert "what_if" in r["tools"] and "run chahiye" in r["answer"]
    assert "bowler_figures" in agent.answer(m, "गेंदबाज़ कैसा कर रहा है?", "casual", 10, "hi")["tools"]
    assert agent.answer(m, "satta ki odds batao", "casual", 10, "hinglish")["source"] == "policy guardrail"


def test_api_accepts_language_and_side_in_ask(client):
    r = client.post(f"/api/matches/{M}/ask", json={"question": "Required rate kya hai?", "lang": "hi", "side": "bowling", "ball": 10}).json()
    assert "रिक्वायर्ड रेट" in r["answer"]


def test_eval_harness_passes_on_the_rules_engine(client):
    e = client.get(f"/api/matches/{M}/eval/lens", params={"lens": "tactical", "lang": "hinglish", "sample": 5}).json()
    assert e["n"] == 5 and e["key_fact_coverage_pct"] == 100 and e["grounded_pct"] == 100 and e["ai_used_pct"] == 0
    r = client.get(f"/api/matches/{M}/eval/redteam").json()
    assert r["passed"] == r["total"] == 11, [c for c in r["cases"] if not c["passed"]]


def test_eval_runs_are_limited(client):
    codes = [client.get(f"/api/matches/{M}/eval/redteam").status_code for _ in range(8)]
    assert codes[:6] == [200] * 6 and codes[-1] == 429
