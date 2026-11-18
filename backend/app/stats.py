"""Stats Centre, Venue Analysis and Fantasy Pulse - all computed from stored deliveries up to the playhead."""
from .model import Match


def compute(m: Match, ball: int) -> dict:
    bat = {n: {"name": n, "runs": r, "balls": b, "fours": 0, "sixes": 0, "gain": 0, "out": None}
           for n, (r, b) in m.init.items()}
    bowl, overs, split = {}, {}, {"four_square": 0, "four_straight": 0, "six_square": 0, "six_straight": 0}
    for d in m.deliveries[:ball]:
        b = bat.setdefault(d["batter"], {"name": d["batter"], "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "gain": 0, "out": None})
        b["balls"] += 1
        b["runs"] += d["runs"]
        b["gain"] += d["runs"]
        b["fours"] += d["runs"] == 4
        b["sixes"] += d["runs"] == 6
        if d["wicket"]:
            b["out"] = d["how"]
        w = bowl.setdefault(d["bowler"], {"name": d["bowler"], "balls": 0, "runs": 0, "wickets": 0, "dots": 0})
        w["balls"] += 1
        w["runs"] += d["runs"]
        w["wickets"] += d["wicket"]
        w["dots"] += (d["runs"] == 0 and not d["wicket"])
        o = overs.setdefault(d["over"], {"over": d["over"] + 1, "runs": 0, "wickets": 0, "balls": 0})
        o["runs"] += d["runs"]
        o["wickets"] += d["wicket"]
        o["balls"] += 1
        if d["region"] and d["runs"] in (4, 6):
            split[("four" if d["runs"] == 4 else "six") + ("_square" if d["region"] == "s" else "_straight")] += 1
    batters = []
    for b in bat.values():
        b["sr"] = round(b["runs"] * 100 / b["balls"]) if b["balls"] else 0
        b["impact"] = b["gain"] + 2 * b["fours"] + 3 * b["sixes"]
        batters.append(b)
    bowlers = []
    for w in bowl.values():
        w["econ"] = round(w["runs"] * 6 / w["balls"], 2) if w["balls"] else 0
        w["impact"] = max(0, round(25 * w["wickets"] + w["dots"] - 0.5 * w["runs"]))
        bowlers.append(w)
    watch = [{"name": b["name"], "role": "Batter", "impact": b["impact"],
              "why": f"{b['runs']} off {b['balls']} (SR {b['sr']}), fours {b['fours']}, sixes {b['sixes']} in this replay"
                     + (f", out {b['out']}" if b["out"] else ", still batting")} for b in batters if b["balls"]] + \
            [{"name": w["name"], "role": "Bowler", "impact": w["impact"],
              "why": f"{w['wickets']}/{w['runs']} from {w['balls']} balls, economy {w['econ']}, dot balls {w['dots']}"} for w in bowlers]
    watch.sort(key=lambda x: -x["impact"])
    return {"batters": sorted(batters, key=lambda b: -b["runs"]), "bowlers": bowlers,
            "runs_by_over": [overs[k] for k in sorted(overs)], "boundaries": split, "venue": m.venue,
            "watchlist": watch[:4],
            "disclaimer": "Sightscreen impact score is an illustrative performance view of a simulated match. It is not official Dream11 points, advice or a prediction."}
