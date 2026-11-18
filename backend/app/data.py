"""Simulated demo match, stored ball-by-ball (event-sourced). All names/venue are fictional."""
import json
from . import db

MATCH_ID = "demo-t20-chase"
START_OVER, VIDEO_OFFSET, SECONDS_PER_BALL = 14, 6, 9
VENUE = ("harbour-oval", "Harbour Oval (fictional)", 74, 62,
         "Fictional venue for the demo: long straight boundary, short square boundaries.", 1)
BAT_INIT = {"Dev Malhotra": [38, 26], "Arjun Rane": [21, 15]}  # runs, balls before the replay window
QUEUE = ["Kabir Sethi", "Vihaan Joshi", "Neel Kulkarni", "Om Desai", "Yash Thakur"]
# token: digit [+ s(quare)/t(raight) for boundaries] or W:<how>
OVERS = [
    ("Rohan Pillai", ["1", "4s", "0", "1", "W:caught at long-on", "2"]),
    ("Imran Qadri", ["1", "0", "6t", "1", "1", "4s"]),
    ("Tanmay Bose", ["4t", "1", "0", "W:bowled", "1", "6s"]),
    ("Siddharth Nair", ["0", "1", "6s", "4s", "W:lbw", "1"]),
    ("Rohan Pillai", ["2", "6t", "0", "4t", "4s", "6s"]),
    ("Imran Qadri", ["1", "0", "W:run out", "0", "1", "2"]),
]
KINDS = {0: "DOT", 1: "SINGLE", 2: "TWO", 4: "FOUR", 6: "SIX"}


def build_deliveries():
    striker, non, queue, out, idx = "Dev Malhotra", "Arjun Rane", list(QUEUE), [], 0
    for n, (bowler, toks) in enumerate(OVERS):
        for b, tok in enumerate(toks, 1):
            idx += 1
            wicket, how, region, runs = tok.startswith("W"), None, None, 0
            if wicket:
                how = tok.split(":")[1]
            else:
                runs, region = int(tok[0]), (tok[1] if len(tok) > 1 else None)
            kind = "WICKET" if wicket else KINDS[runs]
            out.append((MATCH_ID, idx, START_OVER + n, b, bowler, striker, runs, int(wicket), how, kind, region,
                        VIDEO_OFFSET + (idx - 1) * SECONDS_PER_BALL, int(kind in ("WICKET", "FOUR", "SIX"))))
            if wicket:
                striker = queue.pop(0)
            elif runs % 2:
                striker, non = non, striker
            if b == 6:
                striker, non = non, striker
    return out


def seed() -> None:
    db.init()
    with db.conn() as c:
        if c.execute("SELECT 1 FROM matches WHERE id=?", (MATCH_ID,)).fetchone():
            return
        c.execute("INSERT INTO venues VALUES(?,?,?,?,?,?)", VENUE)
        c.execute("INSERT INTO matches VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (MATCH_ID, "Mumbai Meteors v Chennai Comets - the chase (simulated)", "Mumbai Meteors",
                   "Chennai Comets", 182, VENUE[0], 112, 3, START_OVER, 0, json.dumps(BAT_INIT), "SIMULATED DEMO"))
        c.executemany("INSERT INTO deliveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", build_deliveries())
