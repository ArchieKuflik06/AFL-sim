"""
Integration tests: real PlayerEvents/MatchEvents classes driven through a
real ChainTracker, rather than the FakeChainEvent used in
test_chain_tracker.py.
"""
from features.PlayerEvents import (
    KickEvent, HandballEvent, GoalEvent, BehindEvent, Mark, Tackle,
    FreeDisposal, FreeKickReason,
)
from features.MatchEvents import OutOfBounds, EventReview
from tests.conftest import find_player


def test_turnover_flagged_kick_ends_the_chain(tracker, hawks):
    # A kick with is_turnover=True should close the chain with
    # end_reason "turnover".
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")

    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    turnover_kick = KickEvent(sicily, 0.2, 1, hawks, is_effective=False, is_turnover=True)
    tracker.process_chain(turnover_kick)

    assert len(tracker.chains) == 1
    assert tracker.chains[0].end_reason == "turnover"
    assert tracker.get_current_chain() is None


def test_clanger_flagged_handball_ends_the_chain_even_without_turnover_flag(tracker, hawks):
    # is_clanger=True alone (without is_turnover) should also end the
    # chain, via DisposalEvent.ends_chain()'s "is_turnover or is_clanger".
    newcombe = find_player(hawks, "Jai Newcombe")
    clanger = HandballEvent(newcombe, 0.1, 1, hawks, is_effective=False,
                             is_turnover=False, is_clanger=True)
    tracker.process_chain(clanger)

    assert len(tracker.chains) == 1
    assert tracker.chains[0].end_reason == "turnover"


def test_effective_non_turnover_disposal_does_not_end_the_chain(tracker, hawks):
    # An ordinary effective disposal should leave the chain open.
    newcombe = find_player(hawks, "Jai Newcombe")
    kick = KickEvent(newcombe, 0.1, 1, hawks, is_effective=True)
    tracker.process_chain(kick)
    assert tracker.chains == []
    assert tracker.get_current_chain() is not None


def test_real_intercept_mark_by_opposition_triggers_possession_change(tracker, hawks, tigers):
    # A Mark by the opposing team mid-chain should close the current
    # chain via possession_change and start a new one for the intercepting team.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")

    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    intercept = Mark(grimes, 0.2, 1, tigers, is_intercept=True)
    tracker.process_chain(intercept)

    assert len(tracker.chains) == 1
    closed = tracker.chains[0]
    assert closed.team == hawks
    assert closed.end_reason == "possession_change"

    new_chain = tracker.get_current_chain()
    assert new_chain.team == tigers
    assert new_chain.events == [intercept]
    assert new_chain.start_reason == "turnover"


def test_goal_ends_chain_and_resets_next_start_reason_to_center_bounce(tracker, hawks):
    # A goal should close the chain, and the next chain (any team) should
    # start as a centre bounce.
    lewis = find_player(hawks, "Mitch Lewis")
    tracker.process_chain(GoalEvent(lewis, 0.1, 1, hawks, is_effective=True))

    assert tracker.chains[0].end_reason == "goal"
    other_event = KickEvent(lewis, 0.2, 1, hawks, is_effective=True)
    tracker.process_chain(other_event)
    assert tracker.get_current_chain().start_reason == "center_bounce"


def test_behind_ends_chain_and_next_chain_start_reason(tracker, hawks):
    # A behind should close the chain with end_reason "behind"; the next
    # chain's start_reason is checked against actual ChainTracker output.
    lewis = find_player(hawks, "Mitch Lewis")
    tracker.process_chain(BehindEvent(lewis, 0.1, 1, hawks, is_effective=True))

    assert tracker.chains[0].end_reason == "behind"
    next_event = KickEvent(lewis, 0.2, 1, hawks, is_effective=True)
    tracker.process_chain(next_event)
    assert tracker.get_current_chain().start_reason == "kick_in"


def test_tackle_mid_chain_is_recorded_but_does_not_close_it(tracker, hawks, tigers):
    # A tackle event carries the tackling team as its .team, so an
    # opposition tackle still closes the chain via the team-change check
    # (possession_change) — not via Tackle.ends_chain() itself.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")

    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    tackle = Tackle(grimes, newcombe, 0.2, 1, tigers)
    tracker.process_chain(tackle)

    assert tracker.chains[0].end_reason == "possession_change"
    assert tracker.get_current_chain().team == tigers
    assert tracker.get_current_chain().events == [tackle]


def test_tackle_by_same_team_does_not_close_chain(tracker, hawks):
    # A same-team tackle event simply gets appended, since Tackle never
    # overrides ends_chain().
    sicily = find_player(hawks, "James Sicily")
    newcombe = find_player(hawks, "Jai Newcombe")

    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    same_team_tackle = Tackle(sicily, newcombe, 0.2, 1, hawks)
    tracker.process_chain(same_team_tackle)

    assert tracker.chains == []
    assert tracker.get_current_chain().events[-1] is same_team_tackle


def test_free_kick_mid_chain_does_not_close_it(tracker, hawks):
    # A free kick to a player on the currently-in-possession team should
    # be appended without closing the chain.
    gunston = find_player(hawks, "Jack Gunston")
    sicily = find_player(hawks, "James Sicily")

    tracker.process_chain(KickEvent(sicily, 0.1, 1, hawks, is_effective=True))
    fk = FreeDisposal(gunston, sicily, 0.2, 1, hawks, reason=FreeKickReason.HOLDING_BALL)
    tracker.process_chain(fk)

    assert tracker.chains == []
    assert tracker.get_current_chain().events[-1] is fk


def test_fifty_metre_free_kick_is_supported_with_reason(tracker, hawks, tigers):
    # Simulate a 50m free kick by passing the new FIFTY_METRE reason.
    lewis = find_player(hawks, "Mitch Lewis")
    grimes = find_player(tigers, "Dylan Grimes")

    fk = FreeDisposal(lewis, grimes, 0.5, 1, hawks, reason=FreeKickReason.FIFTY_METRE)
    tracker.process_chain(fk)

    assert tracker.get_current_chain() is not None
    assert tracker.get_current_chain().events == [fk]
    assert fk.reason == FreeKickReason.FIFTY_METRE
    assert "50m Free Kick" in fk.display_event()


def test_out_of_bounds_mid_chain_does_not_close_it(tracker, hawks):
    # An out-of-bounds event from the current team should be appended
    # without closing the chain.
    sicily = find_player(hawks, "James Sicily")
    tracker.process_chain(KickEvent(sicily, 0.1, 1, hawks, is_effective=True))
    oob = OutOfBounds(sicily, 0.2, 1, hawks)
    tracker.process_chain(oob)

    assert tracker.chains == []
    assert tracker.get_current_chain().events[-1] is oob


def test_event_review_can_start_a_chain_if_none_is_open(tracker, hawks):
    # EventReview inherits MatchEvent's default ends_chain()->False and
    # has a valid .team, so if fed to process_chain() while no chain is
    # open, it starts a new one-event chain just like any other event.
    lewis = find_player(hawks, "Mitch Lewis")
    goal = GoalEvent(lewis, 0.1, 1, hawks, is_effective=True)
    tracker.process_chain(goal)
    assert tracker.get_current_chain() is None

    review = EventReview(
        match=None, chain_tracker=tracker, player=lewis, time=0.11,
        quarter=1, team=hawks, review_of=None, overturned=True, new_event=None,
    )
    tracker.process_chain(review)

    assert tracker.get_current_chain() is not None
    assert tracker.get_current_chain().events == [review]
