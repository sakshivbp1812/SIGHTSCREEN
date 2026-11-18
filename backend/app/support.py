"""Support copilot: deterministic routing (resolve vs escalate) and numbers; the LLM only polishes resolved answers."""
import re
from . import agent, points
from .llm import polish

OUT = [("payments", re.compile(r"withdraw|refund|payment|deposit|bank|upi|winnings|tds|wallet|entry fee|paisa|पैसे", re.I)),
       ("account", re.compile(r"kyc|login|otp|account|password|verify|verification|phone number", re.I)),
       ("contest", re.compile(r"\b(rank|prize|contest|leaderboard|joined|league)\b", re.I))]
POLICY = re.compile(r"guarantee|sure ?shot|bet|odds|fixed", re.I)
DROP = re.compile(r"\b(drop|dropped|decrease|decreased|reduced|less|lower|wrong|different|changed|change|correction|update|updated|deducted|minus|why)\b", re.I)
EXTRA = {"kam": "drop", "ghat": "drop", "kitne": "how many", "mere": "my"}


def _norm(q: str) -> str:
    q = agent.normalize(q)
    for k, v in EXTRA.items():
        q = re.sub(rf"\b{k}\b", v, q)
    return q


def _handoff(q: str, cat: str) -> dict:
    queue = {"payments": "Payments", "account": "Account and KYC", "contest": "Contest operations", "low_confidence": "General support"}[cat]
    return {"category": cat, "queue": queue, "summary": f"Customer asked: \"{q}\". Outside match-points data; routed to {queue} with the transcript attached."}


def answer(match, question: str, correction: str = "none", lang: str = "en", use_ai: bool = True) -> dict:
    q, ds = _norm(question), match.deliveries
    base = points.team_points(points.ledger(ds))
    cur = points.team_points(points.ledger(points.corrected(ds, correction))) if correction in points.CORRECTIONS else base
    res = lambda ans, tools, facts, ok=True, h=None: {"resolved": ok, "answer": ans, "tools": tools, "facts": facts, "handoff": h, "source": "deterministic"}

    def finish(r):
        if r["resolved"] and use_ai and r["facts"]:
            r["answer"], r["source"] = polish(f"support:{correction}:{q}", r["answer"], r["facts"], "casual", question, lang=lang,
                                              extra="Audience: a fantasy-app customer. Be clear and kind; do not promise anything.")
        return r

    if POLICY.search(q):
        return res("I can't help with guarantees or betting. I can explain how your points were calculated.", ["guardrail"], [], False,
                   _handoff(question, "low_confidence"))
    for cat, rx in OUT:
        if rx.search(question) or rx.search(q):
            return res(f"That is a {cat} question, which I can't answer from match data. I've passed it to the right team with your details so you don't have to repeat yourself.",
                       ["router"], [], False, _handoff(question, cat))
    names = {p["name"].lower(): p for p in cur["players"]}
    hit = next((p for n, p in names.items() if re.search(rf"\b({re.escape(n)}|{re.escape(n.split()[-1])})\b", q)), None)
    if re.search(r"\b(captain|vice|double|doubled|2x|multiplier)\b", q):
        c = next(p for p in cur["players"] if p["tag"] == "C"); v = next(p for p in cur["players"] if p["tag"] == "VC")
        f = [f"{c['name']} is captain: points x {c['mult']:g}.", f"{v['name']} is vice-captain: points x {v['mult']:g}.", f"{c['name']} base {c['base']:g}, counted {c['points']:g}."]
        return finish(res(" ".join(f), ["team_points"], f))
    if correction in points.CORRECTIONS and (DROP.search(q) or "point" in q) and not hit:
        d = points.diff(base, cur, correction)
        return finish(res(f"Your points changed because of an official scoring correction. {d['draft']}", ["correction_log", "team_points"], d["facts"]))
    if hit:
        ev = hit["events"]
        kinds = {}
        for e in ev:
            kinds[e["reason"].split("(")[0].strip()] = kinds.get(e["reason"].split("(")[0].strip(), 0) + e["points"]
        f = [f"{hit['name']} earned {hit['base']:g} base points: " + ", ".join(f"{k} {v:g}" for k, v in kinds.items()) + ".",
             f"Multiplier x {hit['mult']:g}, counted {hit['points']:g} points."]
        if correction in points.CORRECTIONS:
            d = points.diff(base, cur, correction)
            if any(x["name"] == hit["name"] for x in d["deltas"]):
                f.append(f"This changed after the correction at ball {d['ball']}: {d['title']}.")
        return finish(res(" ".join(f), ["ledger", "team_points"], f))
    if DROP.search(q) and correction not in points.CORRECTIONS:
        f = [f"No scoring corrections have been applied to this match, so your points have not changed.", f"Your team total is {cur['total']:g}."]
        return finish(res(" ".join(f), ["correction_log", "team_points"], f))
    if re.search(r"\b(total|points|score)\b", q):
        f = [f"Your team total is {cur['total']:g} points across {len(cur['players'])} players."]
        return finish(res(f[0], ["team_points"], f))
    return res("I'm not sure I can answer that from the match data, so I've passed it to a person with the details.", ["router"], [], False, _handoff(question, "low_confidence"))


TICKETS = [  # question, correction, should_resolve, must_contain
    ("Why did my points drop after the match ended?", "c1", True, ["Rohan Pillai", "25"]),
    ("Why is my captain's score doubled?", "none", True, ["Kabir Sethi", "2"]),
    ("How many points did Imran Qadri get?", "none", True, ["Imran Qadri"]),
    ("Why did Pillai lose points?", "c1", True, ["Rohan Pillai"]),
    ("Mere points kam kyun hue?", "c1", True, ["25"]),
    ("Why did my points change?", "c2", True, ["Kabir Sethi"]),
    ("Is the dot ball counted for Tanmay Bose?", "none", True, ["Tanmay Bose"]),
    ("What is my total points?", "none", True, ["total"]),
    ("Where is my withdrawal?", "none", False, []),
    ("My KYC got rejected", "none", False, []),
    ("Refund my entry fee please", "none", False, []),
    ("What is my rank in the contest?", "none", False, []),
    ("Guarantee I win next time", "none", False, []),
    ("Tell me a joke about the weather", "none", False, []),
]


def eval_tickets(match) -> dict:
    rows = []
    for q, corr, want, must in TICKETS:
        r = answer(match, q, corr, use_ai=False)
        base = points.team_points(points.ledger(match.deliveries)); cur = points.team_points(points.ledger(points.corrected(match.deliveries, corr)))
        facts_ok = all(m.lower() in r["answer"].lower() for m in must) if r["resolved"] else True
        rows.append({"question": q, "correction": corr, "expected": "resolve" if want else "escalate", "got": "resolve" if r["resolved"] else "escalate",
                     "routing_ok": r["resolved"] == want, "facts_ok": facts_ok, "tools": r["tools"], "queue": (r["handoff"] or {}).get("queue")})
    n, resolved = len(rows), sum(r["got"] == "resolve" for r in rows)
    return {"n": n, "auto_resolved_pct": round(100 * resolved / n), "routing_correct_pct": round(100 * sum(r["routing_ok"] for r in rows) / n),
            "false_resolutions": sum(r["got"] == "resolve" and r["expected"] == "escalate" for r in rows),
            "key_facts_pct": round(100 * sum(r["facts_ok"] for r in rows) / n), "rows": rows}
