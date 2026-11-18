"""Catch me up: rank what changed since the fan last looked and brief them in about 30 seconds.
Code selects the moments and computes every number; the LLM (optional) only words the result."""
from . import i18n
from .agent import what_if
from .lens import fact_lines
from .llm import polish
from .model import Match

MODES = {"quick": {"moments": 2, "words": 90}, "full": {"moments": 4, "words": 170}}


def impact(m: Match, i: int) -> int:
    """How much a delivery changed the chase: pressure swing, plus a bonus for a wicket."""
    d, b, a = m.deliveries[i - 1], m.frames[i - 1], m.frames[i]
    return abs(a.pressure - b.pressure) + (10 if d["wicket"] else 0)


def candidates(m: Match, since: int, ball: int) -> list:
    return [i for i in range(since + 1, ball + 1) if m.deliveries[i - 1]["key"]]


def pick(m: Match, since: int, ball: int, k: int) -> list:
    top = sorted(candidates(m, since, ball), key=lambda i: (-impact(m, i), i))[:k]
    return sorted(top)


def moment_text(m: Match, i: int, lang: str) -> str:
    d, a, t = m.deliveries[i - 1], m.frames[i], i18n.T[lang]
    label = f"{m.label(d)}:"
    if d["wicket"]:
        return t["m_w"].format(label=label, batter=d["batter"], how=i18n.how(lang, d["how"]) if lang != "en" else d["how"], need=a.runs_needed, balls=a.balls_remaining)
    kind = d["kind"].lower() if lang == "en" else i18n.kind(lang, d["kind"])
    return t["m_b"].format(label=label, batter=d["batter"], bowler=d["bowler"], kind=kind, need=a.runs_needed, balls=a.balls_remaining)


def build(m: Match, ball: int, since: int = -1, mode: str = "quick", lang: str = "en", side: str = "neutral", use_ai: bool = True) -> dict:
    mode = mode if mode in MODES else "quick"
    lang = lang if lang in i18n.LANGS else "en"
    side = side if side in ("batting", "bowling") else "neutral"
    n = len(m.deliveries)
    ball = max(0, min(ball, n))
    since = max(0, min(since if since >= 0 else ball - 12, ball))
    cfg, t, s = MODES[mode], i18n.T[lang], m.frames[ball]
    ids = pick(m, since, ball, cfg["moments"])
    p0, p1 = m.frames[since].pressure, s.pressure
    facts = [f"Score {s.runs}/{s.wickets} after {s.overs}.{s.balls} overs; need {s.runs_needed} from {s.balls_remaining} balls; required rate {s.required_rate:.2f}; pressure {p1}."]
    sit = t["sit"].format(runs=s.runs, w=s.wickets, ov=f"{s.overs}.{s.balls}", need=s.runs_needed, balls=s.balls_remaining, rrr=f"{s.required_rate:.2f}", p=p1)
    if s.result:
        sit = t["over"].format(result=s.result, runs=s.runs, w=s.wickets)
    moments = [{"idx": i, "ball": m.label(m.deliveries[i - 1]), "kind": m.deliveries[i - 1]["kind"], "impact": impact(m, i), "text": moment_text(m, i, lang)} for i in ids]
    for i in ids:
        facts += fact_lines(m, i)[:3]
    trend = ""
    if ball > since and p0 != p1:
        trend = t["trend_dn" if p1 < p0 else "trend_up"].format(p0=p0, p1=p1)
        if side != "neutral":
            team = m.meta["batting"] if side == "batting" else m.meta["bowling"]
            good = (p1 < p0) == (side == "batting")
            trend += i18n.T.get(lang, i18n.T["en"])["good" if good else "bad"].format(team=team)
        facts.append(f"Pressure moved from {p0} to {p1} since the fan last looked.")
    watch = ""
    if ball < n and not s.result:
        nx = m.deliveries[ball]
        six, wk = what_if(m, ball, 6, False)["after"], what_if(m, ball, 0, True)["after"]
        watch = t["watch"].format(batter=nx["batter"], bowler=nx["bowler"], r0=f"{s.required_rate:.2f}", r1=f"{six['required_rate']:.2f}", p0=s.pressure, p1=wk["pressure"])
        facts.append(f"{nx['batter']} on strike, {nx['bowler']} bowling. A six: required rate {s.required_rate:.2f} to {six['required_rate']:.2f}. A wicket: pressure {s.pressure} to {wk['pressure']}.")

    def compose(ms, w):
        body = (t["miss_h"] + " " + " ".join(x["text"] for x in ms)) if ms else (t["none"] if ball > 0 else "")
        return " ".join(x for x in (sit, body, trend, watch if w else "") if x)

    keep, use_watch = list(moments), True
    text = compose(keep, use_watch)
    while len(text.split()) > cfg["words"] and (use_watch or len(keep) > 1):  # stay inside the word budget
        if use_watch:
            use_watch = False
        else:
            keep = keep[:-1]
        text = compose(keep, use_watch)
    source = "grounded rules engine"
    if use_ai:
        text, source = polish(f"catchup:{m.meta['id']}:{ball}:{since}:{mode}:{lang}:{side}", text, facts, "casual", lang=lang,
                              question="Write a catch-up briefing: where we are, what the fan missed, what to watch.",
                              extra=f"Word limit: {cfg['words']}." + (f" The fan supports {m.meta['batting'] if side == 'batting' else m.meta['bowling']}." if side != "neutral" else ""))
    words = len(text.split())
    return {"ball": ball, "since": since, "mode": mode, "lang": lang, "side": side, "text": text, "source": source, "words": words,
            "read_seconds": max(5, round(words / 3.3)), "moments": keep, "skipped_moments": len(candidates(m, since, ball)) - len(keep), "facts": facts}


def push(m: Match, ball: int, lang: str = "en") -> dict:
    """Payload a notification service would send for a delivery (key moments only)."""
    lang = lang if lang in i18n.LANGS else "en"
    if not 1 <= ball <= len(m.deliveries) or not m.deliveries[ball - 1]["key"]:
        return {"send": False}
    d, a = m.deliveries[ball - 1], m.frames[ball]
    key = "p_w" if d["wicket"] else "p_6" if d["runs"] == 6 else "p_4"
    return {"send": True, "priority": "high" if d["wicket"] else "normal", "title": i18n.T[lang][key].format(w=a.wickets, need=a.runs_needed, balls=a.balls_remaining),
            "body": moment_text(m, ball, lang), "deep_link": f"/?catchup={ball}&lang={lang}", "collapse_key": f"{m.meta['id']}:{(ball - 1) // 6}"}


def sweep(m: Match) -> dict:
    """Deterministic quality sweep over every playhead position, language and mode."""
    checks = {"within_word_limit": 0, "has_key_number": 0, "moments_valid": 0, "top_ranked": 0, "script_ok": 0}
    n, words = 0, []
    for lang in i18n.LANGS:
        for mode, cfg in MODES.items():
            for ball in range(len(m.deliveries) + 1):
                r = build(m, ball, -1, mode, lang, use_ai=False)
                n += 1
                words.append(r["words"])
                s = m.frames[ball]
                need = str(s.runs if s.result else s.runs_needed)
                chosen = [x["idx"] for x in r["moments"]]
                cands = candidates(m, r["since"], ball)
                checks["within_word_limit"] += r["words"] <= cfg["words"]
                checks["has_key_number"] += need in r["text"]
                checks["moments_valid"] += all(i in cands for i in chosen) and len(chosen) <= cfg["moments"]
                checks["top_ranked"] += all(impact(m, i) <= min((impact(m, c) for c in chosen), default=10 ** 9) for i in cands if i not in chosen) or len(chosen) == len(cands)
                checks["script_ok"] += (lang != "hi") or any("\u0900" <= ch <= "\u097f" for ch in r["text"])
    return {"n": n, "pass_pct": {k: round(100 * v / n) for k, v in checks.items()}, "avg_words": round(sum(words) / n), "max_words": max(words),
            "avg_read_seconds": round(sum(words) / n / 3.3)}
