"""Deterministic cricket maths. The AI layer never computes numbers - it only explains these."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class MatchState:
    innings: int = 2
    batting: str = "Mumbai Meteors"
    bowling: str = "Chennai Comets"
    runs: int = 142
    wickets: int = 4
    overs: int = 16
    balls: int = 3
    target: int = 182

    @property
    def legal_balls(self) -> int:
        return self.overs * 6 + self.balls

    @property
    def balls_remaining(self) -> int:
        return max(0, 120 - self.legal_balls)

    @property
    def runs_needed(self) -> int:
        return max(0, self.target - self.runs)

    @property
    def current_rate(self) -> float:
        return round(self.runs / (self.legal_balls / 6), 2) if self.legal_balls else 0.0

    @property
    def required_rate(self) -> float:
        return round(self.runs_needed / (self.balls_remaining / 6), 2) if self.balls_remaining else 0.0

    @property
    def pressure(self) -> int:
        """Heuristic 0-100 chase-pressure index: required rate vs. a par rate that shrinks as wickets fall.
        NOT a win probability - it is a transparent, explainable indicator."""
        if self.result:
            return 0
        par = 3.5 + 0.8 * (10 - self.wickets)
        return max(0, min(100, round(60 * self.required_rate / par)))

    @property
    def result(self) -> Optional[str]:
        if self.runs >= self.target:
            return f"{self.batting} win"
        if self.wickets >= 10 or self.balls_remaining == 0:
            return f"{self.bowling} win"
        return None

    def public(self) -> dict:
        d = asdict(self)
        d.update({
            "overs_display": f"{self.overs}.{self.balls}",
            "balls_remaining": self.balls_remaining,
            "runs_needed": self.runs_needed,
            "current_rate": self.current_rate,
            "required_rate": self.required_rate,
            "pressure": self.pressure,
            "result": self.result,
        })
        return d


def apply_delivery(state: MatchState, runs: int = 0, wicket: bool = False) -> MatchState:
    """Apply one legal delivery. Wides/no-balls are deliberately out of scope for this demo."""
    if state.result:
        return state
    state.runs += runs
    if wicket:
        state.wickets = min(10, state.wickets + 1)
    state.balls += 1
    if state.balls == 6:
        state.overs += 1
        state.balls = 0
    return state


def state_delta(before: MatchState, after: MatchState) -> dict:
    return {
        "runs_added": after.runs - before.runs,
        "wickets_lost": after.wickets - before.wickets,
        "balls_used": after.legal_balls - before.legal_balls,
        "runs_needed_change": before.runs_needed - after.runs_needed,
        "required_rate_before": before.required_rate,
        "required_rate_after": after.required_rate,
        "pressure_before": before.pressure,
        "pressure_after": after.pressure,
    }
