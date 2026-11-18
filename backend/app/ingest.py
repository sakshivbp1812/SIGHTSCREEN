"""Vendor-feed ingestion: two messy vendor schemas -> one canonical event stream, with validation, dedupe,
re-ordering, quarantine and backfill. Reconciled against the reference scorecard."""
from copy import deepcopy
from . import llm
from .engine import MatchState, apply_delivery
from .model import Match

START_OVER = 14


def vendor_a(d: dict) -> dict:    # nested-ish, strings, 1-based balls ("14.3")
    return {"matchId": "demo-t20-chase", "inn": 2, "ov": f"{d['over']}.{d['ball']}", "bat": d["batter"], "bwl": d["bowler"],
            "r": str(d["runs"]), "w": "1" if d["wicket"] else "0", "dismissal": d["how"]}


def vendor_b(d: dict) -> dict:    # flat, typed, 0-based ball in over
    return {"match": "demo", "over": d["over"], "ballInOver": d["ball"] - 1, "striker": d["batter"], "bowler": d["bowler"],
            "runsOffBat": d["runs"], "extras": 0, "isWicket": d["wicket"], "wicketKind": d["how"]}


def _need(p: dict, *keys):
    for k in keys:
        if p.get(k) in (None, ""):
            raise ValueError(f"missing_field:{k}")


def normalise(vendor: str, p: dict) -> dict:
    """Raw vendor payload -> canonical event. Raises ValueError('reason_code') for unusable payloads."""
    if vendor == "A":
        _need(p, "ov", "bat", "bwl", "r", "w")
        over, ball = (int(x) for x in str(p["ov"]).split("."))
        ev = {"over": over, "ball": ball, "batter": p["bat"], "bowler": p["bwl"], "runs": int(p["r"]),
              "wicket": p["w"] in ("1", 1, True), "how": p.get("dismissal")}
    elif vendor == "B":
        _need(p, "over", "ballInOver", "striker", "bowler", "runsOffBat")
        ev = {"over": int(p["over"]), "ball": int(p["ballInOver"]) + 1, "batter": p["striker"], "bowler": p["bowler"],
              "runs": int(p["runsOffBat"]), "wicket": bool(p.get("isWicket")), "how": p.get("wicketKind")}
    else:
        raise ValueError("unknown_vendor")
    if not 0 <= ev["runs"] <= 6:
        raise ValueError("runs_out_of_range")
    if not 1 <= ev["ball"] <= 6:
        raise ValueError("ball_out_of_range")
    ev["pos"] = (ev["over"] - START_OVER) * 6 + ev["ball"]
    return ev


def build_feed(m: Match, inject: bool = True) -> list:
    """Reference deliveries -> raw vendor messages (odd balls from vendor A, even from B), optionally with realistic faults."""
    raw = [("A" if d["idx"] % 2 else "B", (vendor_a if d["idx"] % 2 else vendor_b)(d)) for d in m.deliveries]
    if not inject:
        return raw
    raw[11], raw[12] = raw[12], raw[11]                         # two balls arrive out of order
    vendor, p = raw[19]                                         # ball 20: corrupted runs
    p = dict(p)
    p["runsOffBat" if vendor == "B" else "r"] = 9 if vendor == "B" else "9"
    raw[19] = (vendor, p)
    p = dict(raw[26][1])                                        # ball 27: missing batter
    p.pop("bat", None)
    p.pop("striker", None)
    raw[26] = (raw[26][0], p)
    raw.insert(5, raw[4])                                       # ball 5 delivered twice
    return raw


def run(m: Match, inject: bool = True) -> dict:
    raw, n = build_feed(m, inject), len(m.deliveries)
    seen, buf, incidents, status, samples, max_pos = set(), {}, [], {}, [], 0
    dupes = reordered = 0
    for k, (vendor, payload) in enumerate(raw):
        try:
            ev = normalise(vendor, payload)
        except ValueError as e:
            incidents.append({"severity": "high", "type": "quarantined", "reason": str(e), "message": k + 1, "vendor": vendor, "raw": payload})
            continue
        if len(samples) < 2 and vendor not in [s["vendor"] for s in samples]:
            samples.append({"vendor": vendor, "raw": payload, "canonical": {x: ev[x] for x in ev if x != "pos"}})
        if ev["pos"] in seen:
            dupes += 1
            status[ev["pos"]] = "dup"
            incidents.append({"severity": "low", "type": "duplicate_dropped", "reason": f"ball {ev['over']}.{ev['ball']} received twice", "message": k + 1, "vendor": vendor})
            continue
        if ev["pos"] < max_pos:
            reordered += 1
            status[ev["pos"]] = "reordered"
            incidents.append({"severity": "info", "type": "reordered", "reason": f"ball {ev['over']}.{ev['ball']} arrived late", "message": k + 1, "vendor": vendor})
        max_pos = max(max_pos, ev["pos"])
        seen.add(ev["pos"])
        buf[ev["pos"]] = ev
    backfilled = []
    for pos in range(1, n + 1):                                  # gap timeout: backfill from the secondary (reference) scorecard
        if pos not in buf:
            d = m.deliveries[pos - 1]
            buf[pos] = {"over": d["over"], "ball": d["ball"], "batter": d["batter"], "bowler": d["bowler"], "runs": d["runs"],
                        "wicket": d["wicket"], "how": d["how"], "pos": pos}
            status[pos] = "backfilled"
            backfilled.append(m.label(d))
    s = MatchState(batting=m.meta["batting"], bowling=m.meta["bowling"], target=m.meta["target"], runs=m.meta["start_runs"],
                   wickets=m.meta["start_wkts"], overs=m.meta["start_overs"], balls=m.meta["start_balls"])
    for pos in range(1, n + 1):
        apply_delivery(s, buf[pos]["runs"], buf[pos]["wicket"])
    same = all((buf[p]["batter"], buf[p]["bowler"], buf[p]["runs"], buf[p]["wicket"]) == (m.deliveries[p - 1]["batter"], m.deliveries[p - 1]["bowler"],
                                                                                          m.deliveries[p - 1]["runs"], m.deliveries[p - 1]["wicket"]) for p in range(1, n + 1))
    ref = m.frames[-1]
    ok = same and (s.runs, s.wickets, s.overs, s.balls) == (ref.runs, ref.wickets, ref.overs, ref.balls)
    quarantined = [i for i in incidents if i["type"] == "quarantined"]
    facts = [f"{len(raw)} raw messages from 2 vendors (A: string fields and 1-based balls; B: typed fields and 0-based balls).",
             f"{dupes} duplicate dropped, {reordered} late event re-ordered, {len(quarantined)} quarantined"
             + (f" ({', '.join(q['reason'] for q in quarantined)})" if quarantined else "") + ".",
             f"{len(backfilled)} gap(s) backfilled from the reference scorecard" + (f": {', '.join(backfilled)}." if backfilled else "."),
             f"Rebuilt score {s.runs}/{s.wickets} after {s.overs}.{s.balls} overs; reference {ref.runs}/{ref.wickets}; reconciled {'yes' if ok else 'NO'}."]
    draft = " ".join(facts)
    text, src = llm.polish(f"ops:{inject}", draft, facts, "casual", question="Summarise this feed incident for an operations engineer.", extra="Audience: operations engineer. Be concise.")
    return {"raw_count": len(raw), "accepted": n - len(backfilled), "duplicates": dupes, "reordered": reordered, "quarantined": len(quarantined),
            "backfilled": len(backfilled), "reconciled": ok, "final": {"runs": s.runs, "wickets": s.wickets, "overs": f"{s.overs}.{s.balls}"},
            "reference": {"runs": ref.runs, "wickets": ref.wickets, "overs": f"{ref.overs}.{ref.balls}"},
            "cells": [{"pos": p, "label": m.label(m.deliveries[p - 1]), "status": status.get(p, "ok")} for p in range(1, n + 1)],
            "incidents": incidents, "samples": samples, "summary": {"text": text, "source": src}}
