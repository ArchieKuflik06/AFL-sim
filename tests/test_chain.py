"""
Tests for features/Chain.py: add/remove events, close/resulted_in_score/
scored_from_turnover/points_scored, and both the explicit-flag and
fallback-inference paths for score-involvement and goal-assist attribution.
"""
import pytest

from features.Chain import Chain
from features.PlayerEvents import (
    KickEvent, HandballEvent, GoalEvent, BehindEvent, RushedBehindEvent,
    Hitout, OnePercenter, KnockOns, Tackle,
)
from tests.conftest import FakeChainEvent, find_player, make_roster_team


# ---------------------------------------------------------------------------
# add_event / remove_event
# ---------------------------------------------------------------------------

def test_add_event_appends_in_order(hawks):
    # Events should be stored in the order they're added.
    chain = Chain(hawks, 1, FakeChainEvent(hawks), start_reason="center_bounce")
    e1, e2 = FakeChainEvent(hawks), FakeChainEvent(hawks)
    chain.add_event(e1)
    chain.add_event(e2)
    assert chain.events == [e1, e2]


def test_remove_event(hawks):
    # remove_event() should take the event back out of the list.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    e1 = FakeChainEvent(hawks)
    chain.add_event(e1)
    chain.remove_event(e1)
    assert e1 not in chain.events


# ---------------------------------------------------------------------------
# close / resulted_in_score / scored_from_turnover / points_scored
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("end_reason,expected", [
    ("goal", True),
    ("behind", True),
    ("turnover", False),
    ("possession_change", False),
    ("out_of_bounds", False),
    ("tackle", False),
    ("end_of_match", False),
])
def test_resulted_in_score(hawks, end_reason, expected):
    # resulted_in_score() should be True only for "goal"/"behind" end reasons.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.close(end_reason)
    assert chain.resulted_in_score() is expected


def test_rushed_behind_chain_currently_scores_zero_points(hawks):
    # A chain closed with end_reason "rushed_behind" is NOT counted as
    # scoring by resulted_in_score() (only "goal"/"behind" qualify), so
    # points_scored() returns 0 for it.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.close("rushed_behind")
    assert chain.resulted_in_score() is False
    assert chain.points_scored() == 0


def test_scored_from_turnover_true_when_start_and_end_match(hawks):
    # scored_from_turnover() should be True when the chain both started
    # from a turnover and ended in a score.
    chain = Chain(hawks, 1, FakeChainEvent(hawks), start_reason="turnover")
    chain.close("goal")
    assert chain.scored_from_turnover() is True


def test_scored_from_turnover_false_when_no_score(hawks):
    # No score at the end -> False, even if it started from a turnover.
    chain = Chain(hawks, 1, FakeChainEvent(hawks), start_reason="turnover")
    chain.close("turnover")
    assert chain.scored_from_turnover() is False


def test_scored_from_turnover_false_when_start_reason_differs(hawks):
    # Scored, but didn't start from a turnover -> False.
    chain = Chain(hawks, 1, FakeChainEvent(hawks), start_reason="stoppage")
    chain.close("goal")
    assert chain.scored_from_turnover() is False


def test_points_scored_goal_is_six(hawks):
    # A goal is worth 6 points.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.close("goal")
    assert chain.points_scored() == 6


def test_points_scored_behind_is_one(hawks):
    # A behind is worth 1 point.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.close("behind")
    assert chain.points_scored() == 1


def test_points_scored_non_scoring_chain_is_zero(hawks):
    # A non-scoring chain (e.g. ended by turnover) is worth 0 points.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.close("turnover")
    assert chain.points_scored() == 0


# ---------------------------------------------------------------------------
# get_score_involvement_players — explicit-flag path
# ---------------------------------------------------------------------------

def test_score_involvement_players_empty_when_chain_not_scored(hawks):
    # Even with is_score_involvement flags set, a non-scoring chain
    # should return no involvement players.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(FakeChainEvent(hawks, is_score_involvement=True, player="anyone"))
    chain.close("turnover")
    assert chain.get_score_involvement_players() == []


def test_score_involvement_players_uses_explicit_flags_when_present(hawks):
    # When events carry an explicit is_score_involvement flag, those
    # exact players (in order) should be returned.
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(FakeChainEvent(hawks, player=newcombe, is_score_involvement=True))
    chain.add_event(FakeChainEvent(hawks, player=sicily, is_score_involvement=True))
    chain.add_event(FakeChainEvent(hawks, event_type="goal", player=lewis))
    chain.close("goal")

    assert chain.get_score_involvement_players() == [newcombe, sicily]


def test_score_involvement_players_dedupes_preserving_first_occurrence(hawks):
    # The same player flagged twice should appear only once in the result.
    newcombe = find_player(hawks, "Jai Newcombe")
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(FakeChainEvent(hawks, player=newcombe, is_score_involvement=True))
    chain.add_event(FakeChainEvent(hawks, player=newcombe, is_score_involvement=True))
    chain.close("goal")
    assert chain.get_score_involvement_players() == [newcombe]


# ---------------------------------------------------------------------------
# get_score_involvement_players — fallback inference path (no explicit flags)
# ---------------------------------------------------------------------------

def test_score_involvement_players_falls_back_to_effective_disposals_before_score(hawks):
    # With no explicit flags, the method should fall back to effective
    # kicks/handballs that occurred before the scoring event.
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    chain.add_event(HandballEvent(sicily, 0.2, 1, hawks, is_effective=False))  # ineffective: excluded
    chain.add_event(GoalEvent(lewis, 0.3, 1, hawks, is_effective=True))
    chain.close("goal")

    assert chain.get_score_involvement_players() == [newcombe]


def test_score_involvement_players_ignores_non_disposal_events_before_the_score(hawks):
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(Hitout(newcombe, 0.1, 1, hawks, is_to_advantage=True))
    chain.add_event(KnockOns(sicily, 0.2, 1, hawks))
    chain.add_event(KickEvent(newcombe, 0.3, 1, hawks, is_effective=True))
    chain.add_event(Tackle(sicily, newcombe, 0.4, 1, hawks))
    chain.add_event(GoalEvent(lewis, 0.5, 1, hawks, is_effective=True))
    chain.close("goal")

    assert chain.get_score_involvement_players() == [newcombe]


def test_score_involvement_players_falls_back_to_scorer_when_no_effective_disposals(hawks):
    # If there are no effective disposals before the score, the scorer
    # themselves should be the sole involvement player.
    lewis = find_player(hawks, "Mitch Lewis")
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(GoalEvent(lewis, 0.1, 1, hawks, is_effective=True))
    chain.close("goal")
    assert chain.get_score_involvement_players() == [lewis]


def test_score_involvement_players_empty_when_no_score_event_found(hawks):
    # If the chain is closed as a "goal" but contains no actual goal/
    # behind event, there's no score event index to anchor off, so the
    # result should be empty.
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(FakeChainEvent(hawks, event_type="kick", player="x"))
    chain.close("goal")
    assert chain.get_score_involvement_players() == []


# ---------------------------------------------------------------------------
# get_goal_assist_players
# ---------------------------------------------------------------------------

def test_goal_assist_players_empty_for_behind(hawks):
    # Goal assists only apply to actual goals, not behinds.
    lewis = find_player(hawks, "Mitch Lewis")
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(BehindEvent(lewis, 0.1, 1, hawks, is_effective=True))
    chain.close("behind")
    assert chain.get_goal_assist_players() == []


def test_goal_assist_players_finds_last_effective_disposal_before_goal(hawks):
    # The assist should go to the LAST effective disposal immediately
    # before the goal, not the first one in the chain.
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    chain.add_event(HandballEvent(sicily, 0.2, 1, hawks, is_effective=True))
    chain.add_event(GoalEvent(lewis, 0.3, 1, hawks, is_effective=True))
    chain.close("goal")

    assert chain.get_goal_assist_players() == [sicily]


def test_goal_assist_players_empty_when_no_effective_disposal_precedes_goal(hawks):
    # No effective disposal before the goal -> no assist credited.
    lewis = find_player(hawks, "Mitch Lewis")
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(GoalEvent(lewis, 0.1, 1, hawks, is_effective=True))
    chain.close("goal")
    assert chain.get_goal_assist_players() == []


def test_rushed_behind_is_never_a_goal_assist_source(hawks):
    # RushedBehindEvent's event_type is "rushed_behind", not "goal", so it
    # should never itself register as the assisted score.
    lewis = find_player(hawks, "Mitch Lewis")
    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(RushedBehindEvent(lewis, 0.1, 1, hawks))
    chain.close("rushed_behind")
    assert chain.get_goal_assist_players() == []
