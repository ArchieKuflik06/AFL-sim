"""
Comprehensive tests for every stat that is actually derived FROM chains —
either directly on the Chain object (resulted_in_score, scored_from_turnover,
points_scored, get_score_involvement_players, get_goal_assist_players) or
via CalcTeamStats.on_chain_closed (player score_involvements/goal_assists,
team points_from_* buckets, rushed_behinds).

Distinct from test_chain.py / test_team_stats_calc.py, which test these
methods individually in isolation — this file focuses on MULTI-CHAIN,
MULTI-PLAYER scenarios to catch accumulation bugs, cross-player
contamination, and bucket/scoreboard reconciliation across a whole match.
"""

import pytest

from engines.ChainTracker import ChainTracker
from game_stats.TeamStats import CalcTeamStats
from features.Chain import Chain
from features.PlayerEvents import (
    KickEvent, HandballEvent, Mark, GoalEvent, BehindEvent, RushedBehindEvent,
)
from tests.conftest import FakeChainEvent, find_player


@pytest.fixture
def wired_rig(hawks, tigers):
    # A ChainTracker wired to BOTH teams' CalcTeamStats, matching
    # MatchEngine._dispatch_chain_closed's fan-out pattern, so cross-team
    # accumulation can be tested in one place.
    home_calc = CalcTeamStats(hawks, hawks.current_game_stats)
    away_calc = CalcTeamStats(tigers, tigers.current_game_stats)

    def dispatch(chain):
        home_calc.on_chain_closed(chain)
        away_calc.on_chain_closed(chain)

    tracker = ChainTracker(on_chain_closed=dispatch)
    return hawks, tigers, tracker, home_calc, away_calc


def run(tracker, events):
    # Mirrors MatchEngine.run(): each event applies its own stat effects
    # AND is fed to the chain tracker.
    for e in events:
        e.apply()
        tracker.process_chain(e)


# ---------------------------------------------------------------------------
# Chain-level scoring helpers across every start_reason / end_reason pairing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("start_reason", ["turnover", "kick_in", "stoppage", "center_bounce"])
@pytest.mark.parametrize("end_reason,expected_points", [("goal", 6), ("behind", 1), ("turnover", 0)])
def test_chain_scoring_helpers_matrix(hawks, start_reason, end_reason, expected_points):
    # Every combination of how a chain started and how it ended should
    # produce consistent resulted_in_score()/points_scored() output, and
    # scored_from_turnover() should only be True when both the start
    # reason is "turnover" AND the chain actually scored.
    chain = Chain(hawks, 1, FakeChainEvent(hawks), start_reason=start_reason)
    chain.close(end_reason)

    assert chain.points_scored() == expected_points
    assert chain.resulted_in_score() == (end_reason in ("goal", "behind"))
    assert chain.scored_from_turnover() == (start_reason == "turnover" and end_reason in ("goal", "behind"))


# ---------------------------------------------------------------------------
# score_involvements / goal_assists — multi-player, multi-chain accumulation
# ---------------------------------------------------------------------------

def test_score_involvements_do_not_leak_between_different_players(wired_rig):
    # Two different chains, each with a different involved player, should
    # credit exactly the right player each time — no cross-contamination.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    run(tracker, [
        KickEvent(newcombe, 0.1, 1, hawks, is_clearance=True, is_effective=True),
        GoalEvent(lewis, 0.2, 1, hawks, is_effective=True),
    ])
    run(tracker, [
        KickEvent(sicily, 0.3, 1, hawks, is_i50=True, is_effective=True),
        GoalEvent(lewis, 0.4, 1, hawks, is_effective=True),
    ])

    assert newcombe.current_game_stats.score_involvements == 1
    assert sicily.current_game_stats.score_involvements == 1
    assert lewis.current_game_stats.score_involvements == 0  # scorer never self-credits
    assert lewis.current_game_stats.goals == 2


def test_goal_assists_attribute_correctly_across_two_separate_goals(wired_rig):
    # Two goals in a row, each set up by a different player, should each
    # credit their own assister — not the same one twice.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    run(tracker, [
        KickEvent(newcombe, 0.1, 1, hawks, is_effective=True),
        GoalEvent(lewis, 0.2, 1, hawks, is_effective=True),
    ])
    run(tracker, [
        KickEvent(sicily, 0.3, 1, hawks, is_effective=True),
        GoalEvent(lewis, 0.4, 1, hawks, is_effective=True),
    ])

    assert newcombe.current_game_stats.goal_assists == 1
    assert sicily.current_game_stats.goal_assists == 1
    assert lewis.current_game_stats.goal_assists == 0


def test_score_involvements_accumulate_across_many_chains_for_one_player(wired_rig):
    # A single player who's involved in several separate scoring chains
    # should have their score_involvements add up correctly.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    lewis = find_player(hawks, "Mitch Lewis")

    for i in range(3):
        run(tracker, [
            KickEvent(newcombe, 0.1 + i, 1, hawks, is_effective=True),
            GoalEvent(lewis, 0.2 + i, 1, hawks, is_effective=True),
        ])

    assert newcombe.current_game_stats.score_involvements == 3
    assert lewis.current_game_stats.goals == 3


def test_score_involvements_only_credited_for_the_scoring_teams_players(wired_rig):
    # A Tigers player's involvement in a Hawks scoring chain should never
    # happen structurally (Chain.team gates on_chain_closed), but this
    # confirms a Tigers player untouched by a Hawks chain stays at zero.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    lewis = find_player(hawks, "Mitch Lewis")
    bolton = find_player(tigers, "Shai Bolton")

    run(tracker, [
        KickEvent(newcombe, 0.1, 1, hawks, is_effective=True),
        GoalEvent(lewis, 0.2, 1, hawks, is_effective=True),
    ])

    assert bolton.current_game_stats.score_involvements == 0
    assert bolton.current_game_stats.goal_assists == 0


# ---------------------------------------------------------------------------
# points_from_* team buckets — reachable and unreachable paths, and the
# invariant that the buckets always sum to the team's actual score
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("start_reason", ["turnover", "kick_in", "stoppage", "center_bounce"])
def test_points_from_buckets_always_sum_to_the_scoreboard(wired_rig, start_reason):
    # Regardless of which bucket a chain's points end up credited to,
    # the four points_from_* fields must always sum to the same total as
    # team.score for that team's own scoring chains.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks), start_reason=start_reason)
    goal = GoalEvent(lewis, 0.1, 1, hawks, is_effective=True)
    goal.apply()
    chain.add_event(goal)
    chain.close("goal")
    home_calc.on_chain_closed(chain)

    stats = hawks.current_game_stats
    bucket_total = (
        stats.points_from_turnovers + stats.points_from_kick_ins
        + stats.points_from_stoppage + stats.points_from_center_bounces
    )
    assert bucket_total == hawks.score == 6


def test_points_from_buckets_stay_zero_for_non_scoring_chains(wired_rig):
    # A chain that ends in a turnover (no score) should not add anything
    # to any points_from_* bucket.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")

    run(tracker, [
        KickEvent(newcombe, 0.1, 1, hawks, is_effective=False, is_turnover=True),
    ])

    stats = hawks.current_game_stats
    assert stats.points_from_turnovers == 0
    assert stats.points_from_kick_ins == 0
    assert stats.points_from_stoppage == 0
    assert stats.points_from_center_bounces == 0


def test_points_from_buckets_accumulate_across_multiple_scoring_chains(wired_rig):
    # Several scoring chains closed in sequence for the same team should
    # accumulate their combined point value, however the buckets are split.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    lewis = find_player(hawks, "Mitch Lewis")
    gunston = find_player(hawks, "Jack Gunston")

    run(tracker, [GoalEvent(lewis, 0.1, 1, hawks, is_effective=True)])
    run(tracker, [BehindEvent(gunston, 0.2, 1, hawks, is_effective=True)])
    run(tracker, [GoalEvent(lewis, 0.3, 1, hawks, is_effective=True)])

    stats = hawks.current_game_stats
    bucket_total = (
        stats.points_from_turnovers + stats.points_from_kick_ins
        + stats.points_from_stoppage + stats.points_from_center_bounces
    )
    assert bucket_total == hawks.score == 13  # 6 + 1 + 6


def test_opposition_team_points_buckets_are_untouched_by_this_teams_chains(wired_rig):
    # Hawks scoring should never touch any of the Tigers' points_from_*
    # buckets.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    lewis = find_player(hawks, "Mitch Lewis")

    run(tracker, [GoalEvent(lewis, 0.1, 1, hawks, is_effective=True)])

    stats = tigers.current_game_stats
    assert stats.points_from_turnovers == 0
    assert stats.points_from_kick_ins == 0
    assert stats.points_from_stoppage == 0
    assert stats.points_from_center_bounces == 0


# ---------------------------------------------------------------------------
# rushed_behinds — chain closure behaviour independent of apply()
# ---------------------------------------------------------------------------

def test_rushed_behind_chain_does_not_credit_any_points_bucket(wired_rig):
    # Chain.resulted_in_score() excludes "rushed_behind" (only "goal"/
    # "behind" qualify), so on_chain_closed's resulted_in_score() gate
    # means a rushed-behind-ended chain credits nothing to any bucket.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(RushedBehindEvent(lewis, 0.1, 1, hawks))
    chain.close("rushed_behind")
    home_calc.on_chain_closed(chain)

    stats = hawks.current_game_stats
    assert stats.points_from_turnovers == 0
    assert stats.points_from_kick_ins == 0
    assert stats.points_from_stoppage == 0
    assert stats.points_from_center_bounces == 0


def test_rushed_behind_chain_does_not_credit_score_involvements(wired_rig):
    # Since resulted_in_score() is False for a rushed_behind chain,
    # get_score_involvement_players()/get_goal_assist_players() both
    # return [] and no player stat is touched via on_chain_closed.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    lewis = find_player(hawks, "Mitch Lewis")

    chain = Chain(hawks, 1, FakeChainEvent(hawks))
    chain.add_event(RushedBehindEvent(lewis, 0.1, 1, hawks))
    chain.close("rushed_behind")
    home_calc.on_chain_closed(chain)

    assert lewis.current_game_stats.score_involvements == 0
    assert lewis.current_game_stats.goal_assists == 0


def test_rushed_behind_ends_chain_via_the_tracker_independent_of_apply(wired_rig):
    # Chain-tracking behaviour (ends_chain/chain_end_reason) doesn't
    # depend on apply() having run, so it can be verified through the
    # tracker directly.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    lewis = find_player(hawks, "Mitch Lewis")

    rb = RushedBehindEvent(lewis, 0.1, 1, hawks)
    tracker.process_chain(rb)

    assert tracker.get_current_chain() is None
    assert tracker.chains[-1].end_reason == "rushed_behind"
    assert tracker.chains[-1].team == hawks


# ---------------------------------------------------------------------------
# Full multi-chain match reconciliation
# ---------------------------------------------------------------------------

def test_full_match_scoreboard_reconciles_with_goals_and_behinds_counted(wired_rig):
    # After a realistic run of mixed chains (goals, behinds, turnovers,
    # possession changes) for both teams, each team's final score should
    # equal 6*goals + 1*behinds exactly, and each team's points_from_*
    # buckets should sum to that same score.
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    lewis = find_player(hawks, "Mitch Lewis")
    gunston = find_player(hawks, "Jack Gunston")
    taranto = find_player(tigers, "Tim Taranto")
    bolton = find_player(tigers, "Shai Bolton")
    grimes = find_player(tigers, "Dylan Grimes")

    run(tracker, [
        KickEvent(newcombe, 0.1, 1, hawks, is_clearance=True, is_effective=True),
        GoalEvent(lewis, 0.2, 1, hawks, is_effective=True),
    ])
    run(tracker, [
        KickEvent(taranto, 0.3, 1, tigers, is_clearance=True, is_effective=True),
        BehindEvent(bolton, 0.4, 1, tigers, is_effective=True),
    ])
    run(tracker, [
        KickEvent(gunston, 0.5, 1, hawks, is_effective=False, is_turnover=True),
        Mark(grimes, 0.6, 1, tigers, is_intercept=True),
        GoalEvent(bolton, 0.7, 1, tigers, is_effective=True),
    ])
    run(tracker, [
        GoalEvent(lewis, 0.8, 1, hawks, is_effective=True),
    ])
    tracker.finalize()

    assert hawks.current_game_stats.goals == 2
    assert hawks.current_game_stats.behinds == 0
    assert tigers.current_game_stats.goals == 1
    assert tigers.current_game_stats.behinds == 1

    assert hawks.score == 12
    assert tigers.score == 7

    hawks_stats = hawks.current_game_stats
    hawks_bucket_total = (
        hawks_stats.points_from_turnovers + hawks_stats.points_from_kick_ins
        + hawks_stats.points_from_stoppage + hawks_stats.points_from_center_bounces
    )
    assert hawks_bucket_total == hawks.score

    tigers_stats = tigers.current_game_stats
    tigers_bucket_total = (
        tigers_stats.points_from_turnovers + tigers_stats.points_from_kick_ins
        + tigers_stats.points_from_stoppage + tigers_stats.points_from_center_bounces
    )
    assert tigers_bucket_total == tigers.score


def test_full_match_player_score_involvements_reconcile_with_chain_count(wired_rig):
    # Across a multi-chain match, the total number of score_involvements
    # credited to Hawks players should equal exactly the number of Hawks
    # scoring chains (one involvement credit per unique flagged/inferred
    # player per chain, in these single-assist scenarios).
    hawks, tigers, tracker, home_calc, away_calc = wired_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    lewis = find_player(hawks, "Mitch Lewis")
    sicily = find_player(hawks, "James Sicily")

    run(tracker, [
        KickEvent(newcombe, 0.1, 1, hawks, is_effective=True),
        GoalEvent(lewis, 0.2, 1, hawks, is_effective=True),
    ])
    run(tracker, [
        KickEvent(sicily, 0.3, 1, hawks, is_effective=True),
        BehindEvent(lewis, 0.4, 1, hawks, is_effective=True),
    ])

    total_involvements = (
        newcombe.current_game_stats.score_involvements
        + sicily.current_game_stats.score_involvements
        + lewis.current_game_stats.score_involvements
    )
    hawks_scoring_chains = sum(
        1 for c in tracker.chains if c.team == hawks and c.resulted_in_score()
    )
    assert total_involvements == hawks_scoring_chains == 2