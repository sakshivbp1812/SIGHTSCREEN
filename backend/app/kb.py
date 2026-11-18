"""Small cricket knowledge base for retrieval. Rule entries are plain-English summaries written for this demo;
check the official ICC playing conditions or MCC Laws for exact wording. App entries describe how Sightscreen works."""
RULE_SRC = "Summary written for this demo. Check the ICC playing conditions or MCC Laws for exact wording."
APP_SRC = "Sightscreen documentation"
DOCS = [
    ("R-umpires-call", "Umpire's Call", "When a batter is given out or not out by the on-field umpire and a DRS review is made for LBW, ball-tracking decides whether the original decision stands. If the ball is only clipping the stumps, or the pitching or impact is marginal, the on-field decision stands. This is called Umpire's Call.", "drs review lbw clipping stumps marginal decision third umpire"),
    ("R-free-hit", "Free hit", "After a front-foot no-ball, the next delivery is a free hit. The batter cannot be dismissed in most ways, although a run out is still possible.", "no ball front foot dismissal free hit"),
    ("R-powerplay", "Powerplay in T20", "In a T20 innings the first 6 overs are the powerplay: at most two fielders may be outside the 30-yard circle. After that, at most five fielders may be outside it.", "fielding restrictions circle overs"),
    ("R-super-over", "Super over", "If a limited-overs match is tied, each team can play a one-over innings to decide it, and the team that scores more wins. Tournaments set the rules if the super over is also tied.", "tie tied tiebreak decider"),
    ("R-nrr", "Net run rate", "Net run rate is runs scored per over faced minus runs conceded per over bowled, across the tournament. It separates teams that are level on points.", "nrr tournament table points standings"),
    ("R-dls", "DLS and rain", "Duckworth-Lewis-Stern revises the target when rain or other interruptions shorten a limited-overs innings, using the resources (overs and wickets in hand) each team has. Sightscreen does not compute DLS.", "rain interruption revised target duckworth lewis stern"),
    ("R-lbw", "LBW basics", "A batter can be out lbw if the ball hits the pad or body in line with the stumps (or outside off stump if no shot is offered), would have gone on to hit the stumps, and did not pitch outside leg stump.", "leg before wicket pad stumps"),
    ("R-wide", "Wide ball", "A delivery too wide for the batter to reach by normal means is a wide. One extra run is added and the ball is bowled again.", "wide extras extra run re-bowled"),
    ("R-no-ball", "No-ball", "A no-ball, such as a front-foot no-ball or a dangerous high full toss, adds an extra run and the delivery is bowled again. In limited-overs cricket a front-foot no-ball gives a free hit.", "no ball extras overstep"),
    ("R-hat-trick", "Hat-trick", "A bowler takes a hat-trick by taking three wickets with three consecutive deliveries.", "three wickets consecutive balls hat trick"),
    ("R-economy", "Economy and strike rate", "A bowler's economy is runs conceded per over. A batter's strike rate is runs scored per 100 balls faced.", "economy rate strike rate formula bowler batter"),
    ("R-maiden", "Maiden over", "A maiden over is an over in which the bowler concedes no runs from the bat and bowls no wides or no-balls.", "maiden over no runs"),
    ("R-run-out", "Run out", "A run out happens when a fielder breaks the stumps while a batter is out of their ground. Run outs are not credited to the bowler.", "run out stumps fielder ground bowler credit"),
    ("R-rates", "Overs, required rate and current rate", "An over is six legal deliveries. The required run rate is the runs still needed divided by the overs remaining. The current run rate is runs scored divided by overs faced.", "required rate current rate run rate over balls"),
    ("A-pressure", "How the chase pressure index works", "Pressure is 60 times the required rate divided by (3.5 + 0.8 times the wickets in hand), limited to 0 to 100. It is a transparent heuristic of how hard the chase is, not a win probability.", "pressure index heuristic calculated formula tense intense comfortable"),
    ("A-impact", "How the Sightscreen impact score works", "Illustrative score for the replay: batters earn their runs plus 2 for each four and 3 for each six. Bowlers earn 25 per wicket and 1 per dot ball, minus half a point per run conceded. It is not official Dream11 points.", "impact score standout players fantasy pulse illustrative"),
    ("A-catchup", "How Catch me up chooses moments", "Each key moment since the fan last looked gets an impact score: the swing in the pressure index plus 10 for a wicket. The top two moments (30 seconds) or four (2 minutes) are shown in time order.", "catch me up briefing ranking moments joined late"),
    ("A-points", "Example fantasy-style points rules", "The support copilot uses example rules: 1 per run, plus 1 per four, plus 2 per six, 25 per wicket (not run outs), plus 8 for bowled or lbw, 1 per dot ball. Captain gets 2x and vice-captain 1.5x. These are not official Dream11 scoring rules.", "points rules captain vice captain multiplier scoring support"),
]


def docs():
    return [{"id": i, "title": t, "text": x, "tags": g, "source": RULE_SRC if i.startswith("R-") else APP_SRC} for i, t, x, g in DOCS]
