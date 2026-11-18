from app.engine import MatchState, apply_delivery, state_delta

def test_initial_chase_math():
    s = MatchState()
    assert s.runs_needed == 40
    assert s.balls_remaining == 21
    assert s.public()["overs_display"] == "16.3"
    assert s.required_rate == round(40 / 3.5, 2)

def test_delivery_updates_score_and_over():
    s = MatchState(overs=16, balls=5, runs=100)
    apply_delivery(s, runs=4)
    assert s.runs == 104
    assert (s.overs, s.balls) == (17, 0)

def test_wicket_and_impact():
    before = MatchState()
    after = MatchState()
    apply_delivery(after, wicket=True)
    delta = state_delta(before, after)
    assert after.wickets == 5
    assert delta["wickets_lost"] == 1
    assert delta["balls_used"] == 1


def test_pressure_rises_with_wickets_and_is_bounded():
    a, b = MatchState(wickets=2), MatchState(wickets=8)
    assert b.pressure > a.pressure
    assert 0 <= a.pressure <= 100 and MatchState(runs=182).pressure == 0
