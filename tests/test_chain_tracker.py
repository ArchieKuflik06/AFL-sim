import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engines.ChainTracker import ChainTracker
from features.Chain import Chain
from features.MatchEvents import OutOfBounds
from features.PlayerEvents import ScoreEvent, KickEvent, GoalEvent, Tackle, FreeDisposal, FreeKickReason
from game_stats.Data_Classes import TeamStats, PlayerStats
from game_stats.TeamStats import CalcTeamStats


class DummyPlayer:
    def __init__(self, name="player"):
        self.name = name


class DummyTeam:
    def __init__(self, name="team"):
        self.name = name
        self.score = 0


class TestRushedBehindEvent(ScoreEvent):
    @property
    def event_type(self):
        return "rushed_behind"

    @property
    def score_type(self):
        return "rushed_behind"

    @property
    def score_value(self):
        return 1


def test_score_events_drive_end_reason_and_next_start_reason():
    tracker = ChainTracker()
    event = TestRushedBehindEvent(DummyPlayer(), 10, 1, DummyTeam())

    tracker.process_chain(event)

    assert len(tracker.chains) == 1
    assert tracker.chains[0].end_reason == "rushed_behind"
    assert tracker._next_start_reason == "kick_in"


def test_chain_closed_stats_use_start_reason_mapping():
    team = DummyTeam("home")
    team_stats = TeamStats()
    team.current_game_stats = team_stats
    calc = CalcTeamStats(team, team_stats)
    chain = Chain(team, 1, None, start_reason="stoppage")
    chain.end_reason = "goal"

    calc.on_chain_closed(chain)

    assert team_stats.points_from_stoppage == 6


def test_chain_closed_applies_score_involvement_and_goal_assist_stats():
    team = DummyTeam("home")
    scorer = DummyPlayer("scorer")
    assister = DummyPlayer("assister")
    scorer.current_game_stats = PlayerStats()
    assister.current_game_stats = PlayerStats()

    assist_event = KickEvent(assister, 10, 1, team, is_effective=True)
    goal_event = GoalEvent(scorer, 20, 1, team)
    chain = Chain(team, 1, assist_event, start_reason="turnover")
    chain.add_event(assist_event)
    chain.add_event(goal_event)
    chain.end_reason = "goal"

    team_stats = TeamStats()
    team.current_game_stats = team_stats
    calc = CalcTeamStats(team, team_stats)
    calc.on_chain_closed(chain)

    assert assister.current_game_stats.score_involvements == 1
    assert assister.current_game_stats.goal_assists == 1
    assert team_stats.score_involvements == 1
    assert team_stats.goal_assists == 1


def test_chain_tracker_uses_center_bounce_for_scored_chains():
    team = DummyTeam("home")
    scorer = DummyPlayer("scorer")
    scorer.current_game_stats = PlayerStats()
    goal_event = GoalEvent(scorer, 20, 1, team)
    chain = Chain(team, 1, goal_event, start_reason="turnover")
    chain.add_event(goal_event)
    chain.end_reason = "goal"

    team_stats = TeamStats()
    team.current_game_stats = team_stats
    calc = CalcTeamStats(team, team_stats)
    calc.on_chain_closed(chain)

    assert team_stats.points_from_center_bounces == 6


def test_chain_tracker_treats_out_of_bounds_without_lasso_as_stoppage():
    team = DummyTeam("home")
    player = DummyPlayer("player")
    out_of_bounds = OutOfBounds(player, 10, 1, team)
    chain = Chain(team, 1, out_of_bounds, start_reason="turnover")
    chain.add_event(out_of_bounds)
    chain.end_reason = "out_of_bounds"

    tracker = ChainTracker()
    tracker._next_start_reason = "turnover"
    tracker._end_chain = lambda reason: None

    reason = tracker._infer_start_reason(chain)

    assert reason == "stoppage"


def test_chain_tracker_treats_tackle_without_free_kick_as_stoppage():
    team = DummyTeam("home")
    tackler = DummyPlayer("tackler")
    tackled = DummyPlayer("tackled")
    tackle = Tackle(tackler, tackled, 10, 1, team)
    chain = Chain(team, 1, tackle, start_reason="turnover")
    chain.add_event(tackle)
    chain.end_reason = "tackle"

    tracker = ChainTracker()
    reason = tracker._infer_start_reason(chain)

    assert reason == "stoppage"
