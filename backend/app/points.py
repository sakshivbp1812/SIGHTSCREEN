"""Fantasy-style points engine with an audit ledger and scorer corrections.
EXAMPLE rules only - not official Dream11 scoring. Rules are data so a customer can replace them."""
from copy import deepcopy

RULES = {"run": 1, "four_bonus": 1, "six_bonus": 2, "wicket": 25, "bowled_lbw_bonus": 8, "dot_ball": 1, "captain_x": 2.0, "vice_x": 1.5}
TEAM = [("Kabir Sethi", "Batter", "C"), ("Arjun Rane", "Batter", "VC"), ("Dev Malhotra", "Batter", ""),
        ("Rohan Pillai", "Bowler", ""), ("Imran Qadri", "Bowler", ""), ("Tanmay Bose", "Bowler", "")]
CORRECTIONS = {
    "c1": {"ball": "14.5", "title": "Scorers changed the dismissal at 14.5 from caught at long-on to run out (run outs are not credited to the bowler)",
           "apply": lambda d: d.update(how="run out")},
    "c2": {"ball": "15.6", "title": "Scorers re-scored 15.6 as 4 leg byes instead of 4 runs off the bat",
           "apply": lambda d: d.update(bat_runs=0)},
}


def ledger(deliveries: list, rules: dict = RULES) -> list:
    """One row per points event: (ball, player, role, points, reason)."""
    rows = []
    for d in deliveries:
        ball, br = f"{d['over']}.{d['ball']}", d.get("bat_runs", d["runs"])
        if br:
            rows.append((ball, d["batter"], "Batter", br * rules["run"], f"{br} run(s)"))
        if br == 4:
            rows.append((ball, d["batter"], "Batter", rules["four_bonus"], "four bonus"))
        if br == 6:
            rows.append((ball, d["batter"], "Batter", rules["six_bonus"], "six bonus"))
        if d["wicket"] and d["how"] != "run out":
            rows.append((ball, d["bowler"], "Bowler", rules["wicket"], f"wicket ({d['how']})"))
            if d["how"] in ("bowled", "lbw"):
                rows.append((ball, d["bowler"], "Bowler", rules["bowled_lbw_bonus"], "bowled/lbw bonus"))
        if d["runs"] == 0 and not d["wicket"]:
            rows.append((ball, d["bowler"], "Bowler", rules["dot_ball"], "dot ball"))
    return rows


def team_points(rows: list, rules: dict = RULES, team: list = TEAM) -> dict:
    out = []
    for name, role, tag in team:
        mine = [r for r in rows if r[1] == name]
        base = sum(r[3] for r in mine)
        mult = rules["captain_x"] if tag == "C" else rules["vice_x"] if tag == "VC" else 1
        out.append({"name": name, "role": role, "tag": tag, "mult": mult, "base": base, "points": round(base * mult, 1),
                    "events": [{"ball": r[0], "points": r[3], "reason": r[4]} for r in mine]})
    return {"players": out, "total": round(sum(p["points"] for p in out), 1)}


def corrected(deliveries: list, key: str) -> list:
    ds = deepcopy(deliveries)
    if key in CORRECTIONS:
        for d in ds:
            if f"{d['over']}.{d['ball']}" == CORRECTIONS[key]["ball"]:
                CORRECTIONS[key]["apply"](d)
    return ds


def diff(before: dict, after: dict, key: str) -> dict:
    deltas = [{"name": b["name"], "tag": b["tag"], "mult": b["mult"], "base_delta": a["base"] - b["base"],
               "delta": round(a["points"] - b["points"], 1)} for b, a in zip(before["players"], after["players"]) if a["points"] != b["points"]]
    c = CORRECTIONS[key]
    lines = [f"{x['name']}: {x['delta']:+g} points" + (f" ({x['base_delta']:+g} x {x['mult']:g} for {'captain' if x['tag'] == 'C' else 'vice-captain'})" if x["mult"] != 1 else "")
             for x in deltas]
    facts = [f"Correction at ball {c['ball']}: {c['title']}.", f"Team total {before['total']:g} to {after['total']:g}."] + lines
    return {"key": key, "ball": c["ball"], "title": c["title"], "before": before["total"], "after": after["total"], "deltas": deltas, "facts": facts,
            "draft": " ".join(facts)}
