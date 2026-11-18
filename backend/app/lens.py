"""Live Lens: turns a key delivery into a grounded, fan-friendly insight."""
from .engine import state_delta
from . import i18n
from .llm import polish
from .model import Match

LENSES = ("casual", "tactical", "fantasy")
WINDOW_S = 12  # a key moment stays "live" for this many video seconds


def facts_for(m: Match, i: int) -> dict:
    d, b, a = m.deliveries[i - 1], m.frames[i - 1], m.frames[i]
    nxt = m.deliveries[i] if i < len(m.deliveries) else None
    return {"d": d, "before": b, "after": a, "delta": state_delta(b, a), "next": nxt,
            "bowler": m.bowler_figures(d["bowler"], i), "batter": m.batter_figures(d["batter"], i)}


def fact_lines(m: Match, i: int) -> list:
    f = facts_for(m, i)
    d, b, a, x = f["d"], f["before"], f["after"], f["delta"]
    lines = [f"Ball {m.label(d)}: {d['bowler']} to {d['batter']}, {d['kind']}"
             + (f" ({d['how']})" if d["how"] else "") + f", {d['runs']} run(s).",
             f"Before: {b.runs}/{b.wickets}, need {b.runs_needed} from {b.balls_remaining} balls, required rate {b.required_rate:.2f}.",
             f"After: {a.runs}/{a.wickets}, need {a.runs_needed} from {a.balls_remaining} balls, required rate {a.required_rate:.2f}.",
             f"Chase pressure index (heuristic, not a win probability) moved {x['pressure_before']} to {x['pressure_after']}.",
             f"{d['bowler']} in this replay: {f['bowler']['runs']}/{f['bowler']['wickets']} from {f['bowler']['balls']} balls.",
             f"{d['batter']} now {f['batter']['runs']} off {f['batter']['balls']} balls."]
    if d["region"]:
        v = m.venue
        lines.append(f"Venue ({v['name']}): square boundaries {v['square_m']} m, straight {v['straight_m']} m; "
                     f"this boundary went {'square' if d['region'] == 's' else 'straight'}.")
    return lines


def side_line(m: Match, d: dict, lang: str, side: str) -> str:
    """Fan perspective: is this moment good or bad news for the side the fan supports?"""
    if side not in ("batting", "bowling"):
        return ""
    team = m.meta["batting"] if side == "batting" else m.meta["bowling"]
    good = (d["wicket"] and side == "bowling") or (not d["wicket"] and side == "batting")
    return i18n.T.get(lang, i18n.T["en"])["good" if good else "bad"].format(team=team)


def draft_local(m: Match, i: int, lens: str, lang: str) -> str:
    f = facts_for(m, i)
    d, b, a, x, v = f["d"], f["before"], f["after"], f["delta"], m.venue
    t, nb = i18n.T[lang], (f["next"]["batter"] if f["next"] else None)
    h = i18n.how(lang, d["how"])
    if d["wicket"]:
        core = t["wicket"].format(batter=d["batter"], how=h, bowler=d["bowler"], w=a.wickets, need=a.runs_needed,
                                  balls=a.balls_remaining, rrr=f"{a.required_rate:.2f}")
    else:
        core = t["boundary"].format(batter=d["batter"], bowler=d["bowler"], kind=i18n.kind(lang, d["kind"]), need=a.runs_needed,
                                    balls=a.balls_remaining, rb=f"{b.required_rate:.2f}", ra=f"{a.required_rate:.2f}")
    if d["region"] == "s":
        core += t["sq"].format(m=v["square_m"])
    if d["region"] == "t":
        core += t["st"].format(m=v["straight_m"])
    if lens == "tactical":
        return core + t["tac"].format(p0=x["pressure_before"], p1=x["pressure_after"], bowler=d["bowler"],
                                      r=f["bowler"]["runs"], w=f["bowler"]["wickets"], b=f["bowler"]["balls"])
    if lens == "fantasy":
        who = t["fan_w"].format(nb=nb, batter=d["batter"], runs=f["batter"]["runs"]) if d["wicket"] and nb else \
            t["fan_b"].format(batter=d["batter"], runs=f["batter"]["runs"], balls=f["batter"]["balls"])
        return core + who + t["fan_n"]
    return core + (t["why_w"] if d["wicket"] else t["why_6"] if d["runs"] == 6 else t["why_4"])


def draft(m: Match, i: int, lens: str, lang: str = "en", side: str = "neutral") -> str:
    base = draft_en(m, i, lens) if lang == "en" else draft_local(m, i, lens, lang)
    return base + side_line(m, m.deliveries[i - 1], lang, side)


def draft_en(m: Match, i: int, lens: str) -> str:
    f = facts_for(m, i)
    d, b, a, x, v = f["d"], f["before"], f["after"], f["delta"], m.venue
    if d["kind"] == "WICKET":
        core = (f"{d['batter']} is out ({d['how']}) off {d['bowler']}. {a.wickets} down, {a.runs_needed} needed "
                f"from {a.balls_remaining} balls at {a.required_rate:.2f} an over.")
    else:
        core = (f"{d['batter']} hits a {d['kind'].lower()} off {d['bowler']}. Need {a.runs_needed} from "
                f"{a.balls_remaining}; required rate {b.required_rate:.2f} to {a.required_rate:.2f}.")
    if d["region"] == "s":
        core += f" Square boundaries here are short ({v['square_m']} m)."
    if d["region"] == "t":
        core += f" Straight boundary is long ({v['straight_m']} m), so that carried well."
    nb = f["next"]["batter"] if f["next"] else None
    if lens == "tactical":
        return core + (f" Pressure {x['pressure_before']} to {x['pressure_after']}. {d['bowler']}: "
                       f"{f['bowler']['runs']}/{f['bowler']['wickets']} from {f['bowler']['balls']} balls in this replay.")
    if lens == "fantasy":
        who = f"{nb} is next on strike; {d['batter']} finishes on {f['batter']['runs']}." if d["wicket"] and nb else \
            f"{d['batter']} is on {f['batter']['runs']} off {f['batter']['balls']}."
        return core + f" Role watch: {who} (No points or picks: this is simulated data.)"
    why = "A new batter walks in, so the next balls are risky." if d["wicket"] else \
        ("That takes a big bite out of the target." if d["runs"] == 6 else "Every boundary eases the pressure.")
    return core + " " + why


def insight(m: Match, i: int, lens: str, lang: str = "en", side: str = "neutral", use_cache: bool = True) -> dict:
    lens = lens if lens in LENSES else "casual"
    lang = lang if lang in i18n.LANGS else "en"
    side = side if side in ("batting", "bowling") else "neutral"
    team = {"batting": m.meta["batting"], "bowling": m.meta["bowling"]}.get(side)
    extra = f"The fan supports {team}: keep the emotional tone right for them." if team else ""
    text, src = polish(f"{m.meta['id']}:{i}:{lens}:{lang}:{side}", draft(m, i, lens, lang, side), fact_lines(m, i), lens,
                       lang=lang, extra=extra, use_cache=use_cache)
    return {"ball": m.label(m.deliveries[i - 1]), "idx": i, "text": text, "source": src, "lang": lang,
            "kind": m.deliveries[i - 1]["kind"], "facts": fact_lines(m, i)}


def at_time(m: Match, t: float, lens: str, lang: str = "en", side: str = "neutral") -> dict:
    i = m.ball_at(t)
    if i == 0:
        return {"triggerAlert": False}
    d = m.deliveries[i - 1]
    if not d["key"] or t - d["video_ts"] > WINDOW_S:
        return {"triggerAlert": False, "ball_idx": i}
    return {"triggerAlert": True, "ball_idx": i, **insight(m, i, lens, lang, side)}
