import json
from copy import deepcopy
from functools import lru_cache
from . import db
from .engine import MatchState, apply_delivery


class Match:
    """In-memory view of a stored match: deliveries + a replayed MatchState frame after every ball."""

    def __init__(self, meta: dict, venue: dict, deliveries: list):
        self.meta, self.venue, self.deliveries = meta, venue, deliveries
        s = MatchState(batting=meta["batting"], bowling=meta["bowling"], target=meta["target"],
                       runs=meta["start_runs"], wickets=meta["start_wkts"],
                       overs=meta["start_overs"], balls=meta["start_balls"])
        self.frames = [deepcopy(s)]
        for d in deliveries:
            apply_delivery(s, d["runs"], d["wicket"])
            self.frames.append(deepcopy(s))
        self.init = json.loads(meta["init_json"])

    def label(self, d: dict) -> str:
        return f"{d['over']}.{d['ball']}"

    def bowler_figures(self, name: str, upto: int) -> dict:
        ds = [d for d in self.deliveries[:upto] if d["bowler"] == name]
        return {"name": name, "balls": len(ds), "runs": sum(d["runs"] for d in ds),
                "wickets": sum(d["wicket"] for d in ds)}

    def batter_figures(self, name: str, upto: int) -> dict:
        r, b = self.init.get(name, [0, 0])
        for d in self.deliveries[:upto]:
            if d["batter"] == name:
                r, b = r + d["runs"], b + 1
        return {"name": name, "runs": r, "balls": b}

    def key_indices(self) -> list:
        return [d["idx"] for d in self.deliveries if d["key"]]

    def ball_at(self, t: float) -> int:
        """Number of deliveries whose video timestamp is <= t (playhead position)."""
        return sum(1 for d in self.deliveries if d["video_ts"] <= t)


@lru_cache(maxsize=8)
def load(match_id: str) -> Match:
    with db.conn() as c:
        m = c.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()
        if not m:
            raise KeyError(match_id)
        v = c.execute("SELECT * FROM venues WHERE id=?", (m["venue_id"],)).fetchone()
        ds = c.execute("SELECT * FROM deliveries WHERE match_id=? ORDER BY idx", (match_id,)).fetchall()
    return Match(dict(m), dict(v), [{**dict(d), "wicket": bool(d["wicket"]), "key": bool(d["key"])} for d in ds])
