"""Fan Intelligence Agent: intent -> tool calls over verified data -> grounded answer (+ optional LLM rewrite)."""
import re
from copy import deepcopy
from .engine import apply_delivery, state_delta
from .lens import fact_lines
from . import i18n, rag, stats as stats_mod
from .llm import polish, provider
from .model import Match

BETS = re.compile(r"\b(bet|betting|odds|wager|gamble|guarantee|sure ?shot|fixed)\b", re.I)
FANTASY = re.compile(r"\b(captain|vice[- ]?captain|dream ?11|fantasy|my team|who should i (pick|choose)|best pick|watchlist|differential)\b", re.I)
PROB = re.compile(r"\b(win probability|chance|chances|who will win|likely to win|will they win|probability)\b", re.I)
HI_MAP = {"kyun": "why", "kyon": "why", "kyu": "why", "क्यों": "why", "agar": "if", "अगर": "if", "agla": "next", "अगला": "next",
          "chhakka": "six", "chakka": "six", "छक्का": "six", "chauka": "four", "चौका": "four", "gendbaaz": "bowler", "gendbaz": "bowler",
          "गेंदबाज़": "bowler", "गेंदबाज": "bowler", "ballebaaz": "batter", "बल्लेबाज़": "batter", "बल्लेबाज": "batter", "maidan": "venue",
          "मैदान": "venue", "run rate": "required rate", "रन रेट": "required rate", "रिक्वायर्ड रेट": "required rate", "kaun": "who",
          "कौन": "who", "कप्तान": "captain", "फैंटेसी": "fantasy", "satta": "bet", "सट्टा": "bet", "kitne run": "required rate"}


def normalize(q: str) -> str:
    """Map common Hinglish/Hindi cricket words onto the English intents the router understands."""
    q = q.lower()
    for k, v in HI_MAP.items():
        q = q.replace(k, v)
    return q


RAG_MIN = 5.5  # BM25 score above which a question is treated as a rules/knowledge question
SCEN = [("wicket", (0, True)), ("six", (6, False)), ("four", (4, False)), ("dot", (0, False)), ("single", (1, False))]


def what_if(m: Match, ball: int, runs: int, wicket: bool) -> dict:
    b = m.frames[ball]
    h = deepcopy(b)
    apply_delivery(h, runs, wicket)
    return {"before": b.public(), "after": h.public(), "impact": state_delta(b, h)}


def answer(m: Match, question: str, lens: str, ball: int, lang: str = "en", side: str = "neutral", use_ai: bool = True) -> dict:
    lang = lang if lang in i18n.LANGS else "en"
    q, tools, facts = normalize(question), [], []
    s = m.frames[ball]

    def use(name, *lines):
        tools.append(name)
        facts.extend(lines)

    if BETS.search(q):
        return {"answer": i18n.T[lang]["no_bets"],
                "source": "policy guardrail", "tools": ["guardrail"], "facts": [], "citations": []}
    hits = rag.INDEX.search(q, 1, min_score=RAG_MIN)
    use("match_state", f"Score {s.runs}/{s.wickets} after {s.overs}.{s.balls} overs, target {s.target}; need {s.runs_needed} "
        f"from {s.balls_remaining} balls; required rate {s.required_rate:.2f}, current rate {s.current_rate:.2f}; "
        f"pressure index {s.pressure} (heuristic).")
    if hits:
        use("rules_search", *[f"[{h['id']}] {h['title']}: {h['text']}" for h in hits])
    if PROB.search(q):
        use("honesty_check", "No calibrated win-probability model exists in this demo; only the pressure index is available.")
    if ball > 0 and re.search(r"\b(why|last|just|impact|happened|that|swing|moment)\b", q):
        use("last_delivery_impact", *fact_lines(m, ball))
    d = m.deliveries[ball - 1] if ball > 0 else None
    if d and re.search(r"\b(bowler|bowling|over|economy|figures)\b", q):
        f = m.bowler_figures(d["bowler"], ball)
        use("bowler_figures", f"{f['name']} in this replay: {f['runs']}/{f['wickets']} from {f['balls']} balls.")
    if d and re.search(r"\b(batter|batsman|striker|set|form|innings)\b", q):
        f = m.batter_figures(d["batter"], ball)
        use("batter_figures", f"{f['name']} is {f['runs']} off {f['balls']} balls.")
    if re.search(r"\b(ground|venue|boundary|boundaries|pitch|stadium)\b", q):
        v = m.venue
        use("venue_facts", f"{v['name']}: straight boundary {v['straight_m']} m, square {v['square_m']} m (fictional demo venue).")
    if re.search(r"\b(what if|if)\b", q):
        for word, (r, w) in SCEN:
            if word in q:
                x = what_if(m, ball, r, w)["after"]
                use("what_if", f"If the next ball is a {word}: {x['runs']}/{x['wickets']}, need {x['runs_needed']} from "
                    f"{x['balls_remaining']} balls, required rate {x['required_rate']:.2f}, pressure {x['pressure']}.")
                break
    if FANTASY.search(q) or provider() != "none":
        st = stats_mod.compute(m, ball)
        if FANTASY.search(q):
            use("fantasy_watchlist", *[f"{w['name']} ({w['role']}), impact {w['impact']}: {w['why']}." for w in st["watchlist"][:3]],
                st["disclaimer"])
        else:
            use("match_context", *[f"{w['name']} ({w['role']}), impact {w['impact']}: {w['why']}." for w in st["watchlist"][:3]],
                "Boundaries so far: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in st["boundaries"].items()) + ".",
                "Last deliveries: " + "; ".join(f"{m.label(x)} {x['batter']} {x['kind']}" for x in m.deliveries[max(0, ball - 5):ball]) + ".")
    lens_line = {"casual": "In simple terms: small swings add up quickly in a chase.",
                 "tactical": f"Tactical read: required {s.required_rate:.2f} vs current {s.current_rate:.2f} is the gap batters must close.",
                 "fantasy": "Fantasy lens: watch roles and who is on strike. No official points or picks in this demo."}.get(lens, "")
    draft_txt = " ".join(dict.fromkeys(facts[:1] + facts[-3:])) + " " + lens_line
    if lang != "en":
        t = i18n.T[lang]
        draft_txt = t["state"].format(runs=s.runs, w=s.wickets, ov=f"{s.overs}.{s.balls}", target=s.target, need=s.runs_needed,
                                      balls=s.balls_remaining, rrr=f"{s.required_rate:.2f}", crr=f"{s.current_rate:.2f}", p=s.pressure) + " " + \
            t["l_" + lens].format(rrr=f"{s.required_rate:.2f}", crr=f"{s.current_rate:.2f}") + " " + t["ask_note"]
    team = {"batting": m.meta["batting"], "bowling": m.meta["bowling"]}.get(side)
    if use_ai:
        text, src = polish(f"ask:{m.meta['id']}:{ball}:{lens}:{lang}:{side}:{q}", draft_txt, facts, lens, question, lang=lang,
                           extra=f"The fan supports {team}." if team else "")
    else:
        text, src = draft_txt, "grounded rules engine"
    return {"answer": text, "source": src, "tools": tools, "facts": facts,
            "citations": [{"id": h["id"], "title": h["title"], "source": h["source"], "text": h["text"]} for h in hits]}
