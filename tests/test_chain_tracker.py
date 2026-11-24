
"""
Domain-scenario tests for the ChainTracker, organized around the AFL
possession-chain rulebook: how a chain starts, how it's maintained, how
it terminates, and the trickier edge cases (spoils, arc entries, etc).
 
Each test is commented with the specific AFL scenario it represents and
asserts the actual behaviour of the current ChainTracker/PlayerEvents
implementation for that scenario.
"""
from features.PlayerEvents import (
    KickEvent, HandballEvent, Mark, Tackle, FreeDisposal, FreeKickReason,
    Hitout, GroundBallGet, OnePercenter, KnockOns, GoalEvent, BehindEvent,
)
from features.MatchEvents import OutOfBounds
from tests.conftest import find_player
 
 
# ---------------------------------------------------------------------------
# 1. STARTING A CHAIN
# ---------------------------------------------------------------------------
 
def test_intercept_mark_starts_a_new_chain_for_the_intercepting_team(tracker, hawks, tigers):
    # AFL rule: an opposition kick cleanly marked by a defender starts a
    # brand new chain for the intercepting team.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    intercept = Mark(grimes, 0.2, 1, tigers, is_intercept=True)
    tracker.process_chain(intercept)
 
    new_chain = tracker.get_current_chain()
    assert new_chain.team == tigers
    assert new_chain.events == [intercept]
 
 
def test_loose_ball_get_by_opposition_starts_a_new_chain(tracker, hawks, tigers):
    # AFL rule: a player picking up a loose ball from an opposition
    # mistake (dropped mark, fumble) starts a new chain for their team.
    newcombe = find_player(hawks, "Jai Newcombe")
    taranto = find_player(tigers, "Tim Taranto")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    loose_ball_get = GroundBallGet(taranto, 0.2, 1, tigers)
    tracker.process_chain(loose_ball_get)
 
    assert tracker.chains[-1].end_reason == "possession_change"
    new_chain = tracker.get_current_chain()
    assert new_chain.team == tigers
    assert new_chain.events == [loose_ball_get]
 
 
def test_smother_recovery_by_opposition_starts_a_new_chain(tracker, hawks, tigers):
    # AFL rule: a smothered kick recovered by the smothering team's side
    # (modelled here with OnePercenter, which covers smothers/spoils in
    # this stat model) starts a new chain for that team.
    sicily = find_player(hawks, "James Sicily")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(KickEvent(sicily, 0.1, 1, hawks, is_i50=True, is_effective=True))
    smother = OnePercenter(grimes, 0.2, 1, tigers)
    tracker.process_chain(smother)
 
    new_chain = tracker.get_current_chain()
    assert new_chain.team == tigers
    assert new_chain.events == [smother]
 
 
def test_free_kick_awarded_starts_a_chain_when_none_is_open(tracker, hawks):
    # AFL rule: a free kick starts the recipient team's chain at the
    # moment the whistle blows.
    gunston = find_player(hawks, "Jack Gunston")
    sicily = find_player(hawks, "James Sicily")
 
    fk = FreeDisposal(gunston, sicily, 0.1, 1, hawks, reason=FreeKickReason.HOLDING_BALL)
    tracker.process_chain(fk)
 
    chain = tracker.get_current_chain()
    assert chain.team == hawks
    assert chain.events == [fk]
    assert chain.start_reason == "center_bounce"  # tracker's initial default
 
 
def test_stoppage_clearance_chain_continues_through_the_clean_gather(tracker, hawks):
    # AFL rule: the chain properly "belongs" to whichever player cleanly
    # gathers a hit-out and disposes of it, not the ruckman's tap alone.
    # In this engine any event opens a chain if none is open (including
    # the hitout itself), but what matters for chain integrity is that
    # the clearance kick following it stays in the SAME chain.
    meek = find_player(hawks, "Lloyd Meek")
    newcombe = find_player(hawks, "Jai Newcombe")
 
    hitout = Hitout(meek, 0.1, 1, hawks, is_to_advantage=True)
    tracker.process_chain(hitout)
    clearance = KickEvent(newcombe, 0.2, 1, hawks, is_clearance=True, is_effective=True)
    tracker.process_chain(clearance)
 
    chain = tracker.get_current_chain()
    assert chain.events == [hitout, clearance]
 
 
def test_kick_in_after_a_behind_starts_the_defending_teams_chain(tracker, hawks, tigers):
    # AFL rule: after a behind, the defending team (not the scoring team)
    # restarts play with a kick-in.
    lewis = find_player(hawks, "Mitch Lewis")
    grimes = find_player(tigers, "Dylan Grimes")
 
    behind = BehindEvent(lewis, 0.1, 1, hawks, is_i50=True, is_effective=True)  # Hawks score a behind
    tracker.process_chain(behind)
    assert tracker.get_current_chain() is None  # dead ball, chain fully closed
 
    kick_in = KickEvent(grimes, 0.2, 1, tigers, is_effective=True)  # Tigers defend, they kick in
    tracker.process_chain(kick_in)
 
    chain = tracker.get_current_chain()
    assert chain.team == tigers
    assert chain.events == [kick_in]
 
 
# ---------------------------------------------------------------------------
# 2. MAINTAINING A CHAIN
# ---------------------------------------------------------------------------
 
def test_successive_disposals_by_the_same_team_maintain_one_chain(tracker, hawks):
    # AFL rule: kicks and handballs by the same team are links in the
    # same chain, not separate chains.
    newcombe = find_player(hawks, "Jai Newcombe")
    gunston = find_player(hawks, "Jack Gunston")
    sicily = find_player(hawks, "James Sicily")
 
    k1 = KickEvent(newcombe, 0.1, 1, hawks, is_effective=True)
    h1 = HandballEvent(gunston, 0.2, 1, hawks, is_effective=True)
    k2 = KickEvent(sicily, 0.3, 1, hawks, is_effective=True)
    tracker.process_chain(k1)
    tracker.process_chain(h1)
    tracker.process_chain(k2)
 
    assert tracker.chains == []
    assert tracker.get_current_chain().events == [k1, h1, k2]
 
 
def test_uncontested_mark_by_same_team_maintains_the_chain(tracker, hawks):
    # AFL rule: a teammate marking a kick keeps the same team's chain alive.
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")
 
    kick = KickEvent(sicily, 0.1, 1, hawks, is_i50=True, is_effective=True)
    mark = Mark(lewis, 0.2, 1, hawks, is_i50=True)
    tracker.process_chain(kick)
    tracker.process_chain(mark)
 
    assert tracker.chains == []
    assert tracker.get_current_chain().events == [kick, mark]
 
 
def test_knock_on_by_same_team_maintains_the_chain(tracker, hawks):
    # AFL rule: directing a loose ball to a teammate (a knock-on/tap)
    # without fully gathering it still keeps the chain alive for that team.
    meek = find_player(hawks, "Lloyd Meek")
    newcombe = find_player(hawks, "Jai Newcombe")
 
    knock_on = KnockOns(meek, 0.1, 1, hawks)
    gather = GroundBallGet(newcombe, 0.2, 1, hawks)
    tracker.process_chain(knock_on)
    tracker.process_chain(gather)
 
    assert tracker.chains == []
    assert tracker.get_current_chain().events == [knock_on, gather]
 
 
def test_ground_level_progression_events_maintain_the_chain(tracker, hawks):
    # AFL rule: a player gathering, bouncing, and running with the ball
    # (modelled as a run of GroundBallGet/OnePercenter/disposal events for
    # the same team) is all one continuous chain.
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
 
    events = [
        GroundBallGet(newcombe, 0.1, 1, hawks),
        OnePercenter(sicily, 0.2, 1, hawks),
        KickEvent(newcombe, 0.3, 1, hawks, is_effective=True),
    ]
    for e in events:
        tracker.process_chain(e)
 
    assert tracker.chains == []
    assert tracker.get_current_chain().events == events
 
 
# ---------------------------------------------------------------------------
# 3. ENDING A CHAIN
# ---------------------------------------------------------------------------
 
def test_opposition_intercept_mark_ends_the_chain(tracker, hawks, tigers):
    # AFL rule: an opposition intercept mark ends the chain immediately
    # and hands the new chain to the intercepting team.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    tracker.process_chain(Mark(grimes, 0.2, 1, tigers, is_intercept=True))
 
    assert tracker.chains[-1].team == hawks
    assert tracker.chains[-1].end_reason == "possession_change"
 
 
def test_opposition_loose_ball_get_ends_the_chain(tracker, hawks, tigers):
    # AFL rule: Team A fumbles or misses a target and Team B gathers the
    # loose ball cleanly — Team A's chain ends there.
    newcombe = find_player(hawks, "Jai Newcombe")
    taranto = find_player(tigers, "Tim Taranto")
 
    tracker.process_chain(HandballEvent(newcombe, 0.1, 1, hawks, is_effective=False))
    tracker.process_chain(GroundBallGet(taranto, 0.2, 1, tigers))
 
    assert tracker.chains[-1].team == hawks
    assert tracker.chains[-1].end_reason == "possession_change"
 
 
def test_holding_the_ball_tackle_ends_the_chain_and_awards_a_free_kick(tracker, hawks, tigers):
    # AFL rule: an effective "holding the ball" tackle ends the ball-
    # carrier's team's chain; the umpire's whistle then awards a free
    # kick chain to the tackling team.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    tackle = Tackle(grimes, newcombe, 0.2, 1, tigers)
    tracker.process_chain(tackle)
    free_kick = FreeDisposal(grimes, newcombe, 0.3, 1, tigers, reason=FreeKickReason.HOLDING_BALL)
    tracker.process_chain(free_kick)
 
    assert tracker.chains[0].team == hawks
    assert tracker.chains[0].end_reason == "possession_change"
    chain = tracker.get_current_chain()
    assert chain.team == tigers
    assert chain.events == [tackle, free_kick]
 
 
def test_goal_scored_ends_the_chain_completely(tracker, hawks):
    # AFL rule: a goal ends the chain outright; the next contest is a
    # centre bounce.
    lewis = find_player(hawks, "Mitch Lewis")
    tracker.process_chain(GoalEvent(lewis, 0.1, 1, hawks, is_i50=True, is_effective=True))

    assert tracker.get_current_chain() is None
    assert tracker.chains[-1].end_reason == "goal"


def test_ended_chain_is_printed_when_closed(tracker, hawks, capsys):
    lewis = find_player(hawks, "Mitch Lewis")
    tracker.process_chain(GoalEvent(lewis, 0.1, 1, hawks, is_i50=True, is_effective=True))

    captured = capsys.readouterr()
    assert "Chain ended: team=Hawthorn Hawks" in captured.out
    assert "end_reason=goal" in captured.out
    assert "goal" in captured.out
 

def test_behind_scored_ends_the_chain_completely(tracker, hawks):
    # AFL rule: a behind also ends the chain outright (the minor score
    # is a dead-ball event, not a continuation of play).
    lewis = find_player(hawks, "Mitch Lewis")
    tracker.process_chain(BehindEvent(lewis, 0.1, 1, hawks, is_i50=True, is_effective=True))
 
    assert tracker.get_current_chain() is None
    assert tracker.chains[-1].end_reason == "behind"
 
 
def test_direct_out_of_bounds_kick_is_flagged_as_a_turnover_disposal(tracker, hawks, tigers):
    # AFL rule: a player kicking the ball directly out of bounds without
    # anyone touching it is a turnover against their team, awarding a
    # free kick or throw-in to the opposition. The disposal that goes out
    # on the full is represented here via is_turnover=True (there is no
    # separate "kicked out on the full" flag), which does end the chain.
    sicily = find_player(hawks, "James Sicily")
    kick_oob = KickEvent(sicily, 0.1, 1, hawks, is_effective=False, is_turnover=True)
    tracker.process_chain(kick_oob)
 
    assert tracker.get_current_chain() is None
    assert tracker.chains[-1].end_reason == "turnover"
 
 
def test_boundary_throw_in_after_touched_out_of_bounds_is_recorded_mid_chain(tracker, hawks):
    # AFL rule: the ball going out of bounds after being touched/spoiled
    # stops play for a boundary throw-in. The dedicated OutOfBounds event
    # is recorded, but (per the current chain-ending rules) it does not
    # by itself close the chain unless the next event belongs to the
    # other team.
    sicily = find_player(hawks, "James Sicily")
    tracker.process_chain(KickEvent(sicily, 0.1, 1, hawks, is_effective=True))
    oob = OutOfBounds(sicily, 0.2, 1, hawks)
    tracker.process_chain(oob)
 
    assert tracker.get_current_chain().events[-1] is oob
 
 
# ---------------------------------------------------------------------------
# 4. EDGE CASES
# ---------------------------------------------------------------------------
 
def test_contested_spoil_recovered_by_the_spoiling_team_starts_their_chain(tracker, hawks, tigers):
    # Edge Case 1 (Contested Knock / Spoil): Team B spoils Team A's i50
    # entry and a Team B player gathers the loose ball a few metres away.
    # The spoil (modelled as OnePercenter) ends Team A's chain, and the
    # follow-up gather by the same defending team continues THEIR chain
    # (not a second possession_change).
    sicily = find_player(hawks, "James Sicily")
    grimes = find_player(tigers, "Dylan Grimes")
    astbury_stand_in = find_player(tigers, "Toby Nankervis")  # any second Tigers player
 
    tracker.process_chain(KickEvent(sicily, 0.1, 1, hawks, is_i50=True, is_effective=True))
    spoil = OnePercenter(grimes, 0.2, 1, tigers)
    tracker.process_chain(spoil)
    gather = GroundBallGet(astbury_stand_in, 0.3, 1, tigers)
    tracker.process_chain(gather)
 
    # Only ONE possession_change should have occurred (Hawks -> Tigers);
    # the spoil and the gather both belong to Tigers, so they sit in the
    # same chain together.
    assert len([c for c in tracker.chains if c.end_reason == "possession_change"]) == 1
    assert tracker.get_current_chain().team == tigers
    assert tracker.get_current_chain().events == [spoil, gather]
 
 
def test_forward_50_arc_entry_does_not_split_the_chain(tracker, hawks):
    # Edge Case 3 (Forward 50 Arc Entry): this engine keeps one organic
    # possession chain all the way to a score/turnover/stoppage — it does
    # not split a "Transition Chain" from a "Forward 50 Chain" at the arc.
    # An is_i50=True disposal is just another link in the same chain.
    newcombe = find_player(hawks, "Jai Newcombe")
    sicily = find_player(hawks, "James Sicily")
 
    k1 = KickEvent(newcombe, 0.1, 1, hawks, is_clearance=True, is_effective=True)
    k2 = KickEvent(sicily, 0.2, 1, hawks, is_i50=True, is_effective=True)  # crosses the arc
    tracker.process_chain(k1)
    tracker.process_chain(k2)
 
    assert tracker.chains == []
    assert tracker.get_current_chain().events == [k1, k2]
 
 
def test_gray_area_fumble_sequence_still_alternates_possession_by_team(tracker, hawks, tigers):
    # Edge Case 2 (Gray Area Fumble): true AFL logic keeps Team A's chain
    # alive if Team B only touches/taps the loose ball without gathering
    # it. This engine has no "touch without control" distinction — every
    # event is attributed outright to event.team, so a Team B event
    # recorded in between (however brief the touch) still flips
    # possession for chain-tracking purposes.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
    sicily = find_player(hawks, "James Sicily")
 
    tracker.process_chain(HandballEvent(newcombe, 0.1, 1, hawks, is_effective=False))  # fumble
    tracker.process_chain(OnePercenter(grimes, 0.2, 1, tigers))  # Tigers touch/tap only
    tracker.process_chain(GroundBallGet(sicily, 0.3, 1, hawks))  # Hawks recover it right back
 
    reasons = [c.end_reason for c in tracker.chains]
    assert reasons == ["possession_change", "possession_change"]
    assert tracker.get_current_chain().team == hawks
 
 
# ---------------------------------------------------------------------------
# 5. FURTHER SCENARIOS DERIVED FROM THE RULES (not literal doc examples)
# ---------------------------------------------------------------------------
 
def test_free_kick_paid_against_the_team_in_possession_ends_their_chain(tracker, hawks, tigers):
    # Rule-derived (Section 1B): a free kick doesn't only START a chain
    # when none is open — if it's paid AGAINST the team currently holding
    # the ball, the whistle transfers the chain to the fouled-against
    # team immediately, same as any other team-change event.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    free_kick = FreeDisposal(grimes, newcombe, 0.2, 1, tigers, reason=FreeKickReason.HIGH_CONTACT)
    tracker.process_chain(free_kick)
 
    assert tracker.chains[-1].team == hawks
    assert tracker.chains[-1].end_reason == "possession_change"
    new_chain = tracker.get_current_chain()
    assert new_chain.team == tigers
    assert new_chain.events == [free_kick]
 
 
def test_rapid_chain_of_turnovers_produces_one_chain_per_possession(tracker, hawks, tigers):
    # Rule-derived (Section 1A + 3A): several turnovers in quick
    # succession should each close the previous chain and open a fresh
    # one for whichever team the ball goes to next — a stress test of
    # possession alternating multiple times in a short passage.
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
    sicily = find_player(hawks, "James Sicily")
    bolton = find_player(tigers, "Shai Bolton")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))       # Hawks chain 1
    tracker.process_chain(Mark(grimes, 0.2, 1, tigers, is_intercept=True))             # -> Tigers chain 2
    tracker.process_chain(GroundBallGet(sicily, 0.3, 1, hawks))                        # -> Hawks chain 3
    tracker.process_chain(Mark(bolton, 0.4, 1, tigers, is_intercept=True))             # -> Tigers chain 4
 
    teams_in_order = [c.team.name for c in tracker.chains]
    assert teams_in_order == ["Hawthorn Hawks", "Richmond Tigers", "Hawthorn Hawks"]
    assert all(c.end_reason == "possession_change" for c in tracker.chains)
    assert tracker.get_current_chain().team == tigers
 
 
def test_consecutive_behinds_each_fully_close_their_own_chain(tracker, hawks, tigers):
    # Rule-derived (Section 3B + 1D): if the defending team's kick-in
    # itself results in another behind, each behind is its own complete,
    # independent chain — there's no "carry-over" state between them.
    lewis = find_player(hawks, "Mitch Lewis")
    bolton = find_player(tigers, "Shai Bolton")
 
    tracker.process_chain(BehindEvent(lewis, 0.1, 1, hawks, is_i50=True, is_effective=True))
    assert tracker.get_current_chain() is None
 
    tracker.process_chain(BehindEvent(bolton, 0.2, 1, tigers, is_i50=True, is_effective=True))
    assert tracker.get_current_chain() is None
 
    assert [c.end_reason for c in tracker.chains] == ["behind", "behind"]
    assert [c.team.name for c in tracker.chains] == ["Hawthorn Hawks", "Richmond Tigers"]
 
 
def test_running_it_out_of_the_square_starts_the_chain_the_same_way_a_kick_in_does(tracker, hawks, tigers):
    # Rule-derived (Section 1D, "All-Clear Play On"): the engine has no
    # separate event type for "ran it out" vs "kicked it in" — a
    # handball by the defending player immediately after a behind starts
    # their chain exactly like a KickEvent would.
    lewis = find_player(hawks, "Mitch Lewis")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(BehindEvent(lewis, 0.1, 1, hawks, is_i50=True, is_effective=True))
    play_on = HandballEvent(grimes, 0.2, 1, tigers, is_effective=True)
    tracker.process_chain(play_on)
 
    chain = tracker.get_current_chain()
    assert chain.team == tigers
    assert chain.events == [play_on]
 
 
def test_long_maintained_chain_preserves_every_link_in_order(tracker, hawks):
    # Rule-derived (Section 2, all sub-rules combined): a single
    # possession chain can legitimately contain many different event
    # types back to back for the same team — hitout, ground ball get,
    # one percenter, knock on, disposals, and a mark — and none of them
    # should split the chain.
    meek = find_player(hawks, "Lloyd Meek")
    newcombe = find_player(hawks, "Jai Newcombe")
    gunston = find_player(hawks, "Jack Gunston")
    sicily = find_player(hawks, "James Sicily")
    lewis = find_player(hawks, "Mitch Lewis")
 
    events = [
        Hitout(meek, 0.01, 1, hawks, is_to_advantage=True),
        GroundBallGet(newcombe, 0.02, 1, hawks),
        KnockOns(gunston, 0.03, 1, hawks),
        OnePercenter(sicily, 0.04, 1, hawks),
        KickEvent(newcombe, 0.05, 1, hawks, is_clearance=True, is_effective=True),
        HandballEvent(gunston, 0.06, 1, hawks, is_effective=True),
        KickEvent(sicily, 0.07, 1, hawks, is_i50=True, is_effective=True),
        Mark(lewis, 0.08, 1, hawks, is_i50=True, is_contested=True),
    ]
    for e in events:
        tracker.process_chain(e)
 
    assert tracker.chains == []
    assert tracker.get_current_chain().events == events
 
 
def test_stoppage_ball_up_after_a_tackle_with_no_free_kick_hands_the_chain_to_the_tackler(tracker, hawks, tigers):
    # Rule-derived (Section 3C): when a tackle results in a ball-up
    # rather than a free kick, the tackling team's next action still
    # opens their own new chain (the model has no distinct "neutral
    # ball-up" state — whichever team acts next owns the chain).
    newcombe = find_player(hawks, "Jai Newcombe")
    grimes = find_player(tigers, "Dylan Grimes")
 
    tracker.process_chain(KickEvent(newcombe, 0.1, 1, hawks, is_effective=True))
    tackle = Tackle(grimes, newcombe, 0.2, 1, tigers)
    tracker.process_chain(tackle)
    next_clearance = KickEvent(grimes, 0.3, 1, tigers, is_clearance=True, is_effective=True)
    tracker.process_chain(next_clearance)
 
    assert tracker.chains[0].team == hawks
    assert tracker.chains[0].end_reason == "possession_change"
    chain = tracker.get_current_chain()
    assert chain.team == tigers
    assert chain.events == [tackle, next_clearance]
 






