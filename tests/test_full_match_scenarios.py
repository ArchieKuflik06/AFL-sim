"""
End-to-end scenario tests: real events, a real ChainTracker, and BOTH
CalcTeamStats instances wired together the way MatchEngine dispatches
chain closures, run over a short synthetic quarter of AFL-style play.

Also covers RushedBehindEvent and Spoil directly, since neither
"rushed_behind" nor "spoil" is registered in EventLoader.CLASS_MAP and so
can't be exercised through a JSON-driven events file.
"""
import pytest

from engines.ChainTracker import ChainTracker
from engines.EventLoader import EventLoader
from game_stats.TeamStats import CalcTeamStats
from features.Match import Match
from features.PlayerEvents import (
    KickEvent, HandballEvent, Mark, GoalEvent, BehindEvent, RushedBehindEvent,
    Tackle, FreeDisposal, FreeKickReason, Spoil, Hitout,
)
from tests.conftest import find_player


@pytest.fixture
def match_rig(hawks, tigers):
    # Wires a ChainTracker to both teams' CalcTeamStats, matching
    # MatchEngine._dispatch_chain_closed's fan-out pattern.
    home_calc = CalcTeamStats(hawks, hawks.current_game_stats)
    away_calc = CalcTeamStats(tigers, tigers.current_game_stats)

    def dispatch(chain):
        home_calc.on_chain_closed(chain)
        away_calc.on_chain_closed(chain)

    tracker = ChainTracker(on_chain_closed=dispatch)
    return hawks, tigers, tracker, home_calc, away_calc


def run(tracker, events):
    # Mirrors MatchEngine.run(): each event must both apply its own stat
    # effects AND be fed to the chain tracker.
    for e in events:
        e.apply()
        tracker.process_chain(e)


def test_realistic_quarter_of_play_scoreboard_matches_event_totals(match_rig):
    # Runs a multi-chain passage of play (clearance->goal, stoppage->
    # behind, turnover->intercept->goal) and checks the resulting
    # scoreboard/stat totals match the events applied.
    hawks, tigers, tracker, home_calc, away_calc = match_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    gunston = find_player(hawks, "Jack Gunston")
    lewis = find_player(hawks, "Mitch Lewis")
    meek = find_player(hawks, "Lloyd Meek")

    taranto = find_player(tigers, "Tim Taranto")
    bolton = find_player(tigers, "Shai Bolton")
    grimes = find_player(tigers, "Dylan Grimes")
    nankervis = find_player(tigers, "Toby Nankervis")

    events = [
        # Chain 1: Hawks centre bounce clearance -> goal
        Hitout(meek, 0.01, 1, hawks, is_to_advantage=True),
        KickEvent(newcombe, 0.02, 1, hawks, is_clearance=True, is_effective=True),
        HandballEvent(gunston, 0.03, 1, hawks, is_effective=True),
        KickEvent(sicily, 0.04, 1, hawks, is_i50=True, is_effective=True),
        Mark(lewis, 0.05, 1, hawks, is_i50=True, is_contested=True),
        GoalEvent(lewis, 0.06, 1, hawks, is_i50=True, is_effective=True),

        # Chain 2: Tigers centre bounce -> tackled -> free kick -> behind
        Hitout(nankervis, 0.07, 1, tigers, is_to_advantage=False),
        KickEvent(taranto, 0.08, 1, tigers, is_clearance=True, is_effective=True),
        Tackle(sicily, taranto, 0.09, 1, hawks),
        FreeDisposal(taranto, sicily, 0.10, 1, tigers, reason=FreeKickReason.HOLDING_BALL),
        KickEvent(taranto, 0.11, 1, tigers, is_i50=True, is_effective=True),
        Mark(bolton, 0.12, 1, tigers, is_i50=True),
        BehindEvent(bolton, 0.13, 1, tigers, is_i50=True),

        # Chain 3: Hawks kick-in, turns over, Tigers intercept, score
        KickEvent(sicily, 0.14, 1, hawks, is_effective=False, is_turnover=True),
        Mark(grimes, 0.15, 1, tigers, is_intercept=True),
        KickEvent(grimes, 0.16, 1, tigers, is_i50=True, is_effective=True),
        GoalEvent(bolton, 0.17, 1, tigers, is_i50=True, is_effective=True),
    ]
    run(tracker, events)
    tracker.finalize()

    assert len(tracker.chains) == 6

    assert hawks.current_game_stats.goals == 1
    assert hawks.current_game_stats.behinds == 0
    assert tigers.current_game_stats.goals == 1
    assert tigers.current_game_stats.behinds == 1

    assert hawks.score == 6
    assert tigers.score == 7

    assert lewis.current_game_stats.goals == 1
    assert bolton.current_game_stats.goals == 1
    assert bolton.current_game_stats.behinds == 1


def test_event_loader_parses_fifty_metre_free_kick_reason(hawks, tigers):
    match = Match(hawks, tigers, "MCG")
    tracker = ChainTracker()
    loader = EventLoader(match, tracker)

    raw_event = {
        "event_type": "free_kick",
        "time": 0.1,
        "quarter": 1,
        "team": "Hawthorn Hawks",
        "got_free_kick_player": "Jai Newcombe",
        "committed_free_kick_player": "Mitch Lewis",
        "reason": "FIFTY_METRE",
    }

    event = loader.load_event(raw_event)

    assert isinstance(event, FreeDisposal)
    assert event.reason == FreeKickReason.FIFTY_METRE
    assert "50m Free Kick" in event.display_event()


def test_score_involvement_inference_across_a_realistic_chain_without_explicit_flags(match_rig):
    # No is_score_involvement/is_goal_assist flags are set anywhere here;
    # CalcTeamStats must fall back to Chain's effective-disposal inference.
    hawks, tigers, tracker, home_calc, away_calc = match_rig
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")

    events = [
        KickEvent(newcombe, 0.01, 1, hawks, is_clearance=True, is_effective=True),
        KickEvent(sicily, 0.02, 1, hawks, is_i50=True, is_effective=True),
        GoalEvent(lewis, 0.03, 1, hawks, is_i50=True, is_effective=True),
    ]
    run(tracker, events)

    assert newcombe.current_game_stats.score_involvements == 1
    assert sicily.current_game_stats.score_involvements == 1
    assert lewis.current_game_stats.score_involvements == 0
    assert sicily.current_game_stats.goal_assists == 1
    assert newcombe.current_game_stats.goal_assists == 0


def test_multi_quarter_match_chains_and_time_winning(match_rig):
    # Runs goals across two quarters and checks time_winning accrual and
    # chain quarter-tagging behave as expected.
    hawks, tigers, tracker, home_calc, away_calc = match_rig
    lewis = find_player(hawks, "Mitch Lewis")
    bolton = find_player(tigers, "Shai Bolton")

    goal_q1 = GoalEvent(lewis, 0.5, 1, hawks, is_effective=True)
    goal_q1.apply()
    tracker.process_chain(goal_q1)
    home_calc.calculate_time_winning(hawks.score > tigers.score, time_delta=10)
    away_calc.calculate_time_winning(tigers.score > hawks.score, time_delta=10)

    goal_q2a = GoalEvent(bolton, 0.5, 2, tigers, is_effective=True)
    goal_q2a.apply()
    tracker.process_chain(goal_q2a)
    goal_q2b = GoalEvent(bolton, 1.0, 2, tigers, is_effective=True)
    goal_q2b.apply()
    tracker.process_chain(goal_q2b)
    home_calc.calculate_time_winning(hawks.score > tigers.score, time_delta=15)
    away_calc.calculate_time_winning(tigers.score > hawks.score, time_delta=15)

    assert hawks.score == 6
    assert tigers.score == 12
    assert hawks.current_game_stats.time_winning == 10
    assert tigers.current_game_stats.time_winning == 15
    assert len(tracker.chains) == 3

    assert tracker.chains[0].quarter == 1
    assert tracker.chains[1].quarter == 2


# ---------------------------------------------------------------------------
# RushedBehindEvent — not reachable via EventLoader.CLASS_MAP, tested directly
# ---------------------------------------------------------------------------

def test_rushed_behind_is_not_player_attributed(hawks):
    # is_player_attributed should be False for a rushed behind.
    lewis = find_player(hawks, "Mitch Lewis")
    rb = RushedBehindEvent(lewis, 0.1, 1, hawks)
    assert rb.is_player_attributed is False
    assert rb.event_type == "rushed_behind"


def test_rushed_behind_apply_raises_type_error(hawks):
    # ScoreEvent.apply()'s non-player-attributed branch calls
    # self._increment_team_stats(self._stat_key, amount=amount), but
    # _increment_team_stats() only accepts *stat_names (no amount kwarg),
    # so calling apply() on a RushedBehindEvent currently raises TypeError.
    rb = RushedBehindEvent(find_player(hawks, "Mitch Lewis"), 0.1, 1, hawks)
    with pytest.raises(TypeError):
        rb.apply()


def test_rushed_behind_ends_chain_with_its_own_reason(tracker, hawks):
    # ends_chain()/chain_end_reason don't depend on apply(), so chain
    # behaviour can still be tested even though apply() itself raises.
    lewis = find_player(hawks, "Mitch Lewis")
    rb = RushedBehindEvent(lewis, 0.1, 1, hawks)
    assert rb.ends_chain() is True
    assert rb.chain_end_reason == "rushed_behind"

    tracker.process_chain(rb)
    assert tracker.chains[0].end_reason == "rushed_behind"
    next_event = KickEvent(lewis, 0.2, 1, hawks, is_effective=True)
    tracker.process_chain(next_event)
    assert tracker.get_current_chain().start_reason == "kick_in"


# ---------------------------------------------------------------------------
# Spoil — also outside EventLoader.CLASS_MAP, tested directly for completeness
# ---------------------------------------------------------------------------

def test_spoil_increments_shared_stats_and_rating(hawks):
    # apply() should increment both player and team spoil counts, and
    # update the player's rating by RatingWeightings.spoils.
    sicily = find_player(hawks, "James Sicily")
    spoil = Spoil(sicily, 0.1, 1, hawks)
    spoil.apply()

    assert sicily.current_game_stats.spoils == 1
    assert hawks.current_game_stats.spoils == 1
    assert sicily.current_game_stats.rating_delta == pytest.approx(0.5)


def test_spoil_fantasy_points_raises_for_missing_weighting(hawks):
    # FantasyWeightings has no "spoil" key defined, so apply_fantasy()
    # should raise AttributeError.
    sicily = find_player(hawks, "James Sicily")
    spoil = Spoil(sicily, 0.1, 1, hawks)
    with pytest.raises(AttributeError):
        spoil.apply_fantasy()
