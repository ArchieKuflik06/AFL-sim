"""
Shared fixtures for the ChainTracker / stats test suite.

Place this `tests/` directory alongside your existing top-level packages
(`features/`, `engines/`, `builders/`, `game_stats/`) and run with:

    pytest tests/ -v
"""
import pytest

from features.player import Player
from features.team import Team


def make_roster_team(name, player_specs):
    # Builds a real Team + real Player objects from a list of
    # (name, number, position) tuples, so every test works against the
    # actual Player/Team classes rather than hand-rolled doubles.
    starters = [Player(n, num, pos, None) for n, num, pos in player_specs]
    team = Team(name, starters, [], 0)
    for p in team.players:
        p.team = team
    return team


@pytest.fixture
def hawks():
    # A small Hawthorn Hawks roster covering the positions used across
    # the suite (mid, forward, defender, ruck).
    return make_roster_team("Hawthorn Hawks", [
        ("Jai Newcombe", 6, "Midfield"),
        ("Mitch Lewis", 14, "Forward"),
        ("James Sicily", 4, "Defender"),
        ("Jack Gunston", 2, "Forward"),
        ("Lloyd Meek", 21, "Ruck"),
    ])


@pytest.fixture
def tigers():
    # A matching Richmond Tigers roster, used as the "opposition" team
    # for possession-change / turnover / cross-team tests.
    return make_roster_team("Richmond Tigers", [
        ("Tim Taranto", 3, "Midfield"),
        ("Shai Bolton", 7, "Forward"),
        ("Dylan Grimes", 8, "Defender"),
        ("Tom Lynch", 9, "Forward"),
        ("Toby Nankervis", 17, "Ruck"),
    ])


class ChainCloseRecorder:
    # Records every chain handed to on_chain_closed, in order, so tests
    # can assert both WHICH chains closed and in WHAT sequence.
    def __init__(self):
        self.chains = []

    def __call__(self, chain):
        self.chains.append(chain)


@pytest.fixture
def recorder():
    return ChainCloseRecorder()


@pytest.fixture
def tracker(recorder):
    # A ChainTracker wired to the recorder above.
    from engines.ChainTracker import ChainTracker
    return ChainTracker(on_chain_closed=recorder)


@pytest.fixture
def home_calc(hawks):
    # CalcTeamStats for the Hawks, matching how MatchEngine wires it up.
    from game_stats.TeamStats import CalcTeamStats
    return CalcTeamStats(hawks, hawks.current_game_stats)


@pytest.fixture
def away_calc(tigers):
    # CalcTeamStats for the Tigers.
    from game_stats.TeamStats import CalcTeamStats
    return CalcTeamStats(tigers, tigers.current_game_stats)


def find_player(team, name):
    # Convenience lookup so tests can grab a specific roster player by name.
    return next(p for p in team.players if p.name == name)


class FakeChainEvent:
    """
    Minimal stand-in implementing exactly the surface ChainTracker/Chain
    touch via duck typing: .team, .quarter, .ends_chain(), .chain_end_reason,
    plus optional .event_type/.player/.is_effective/.is_score_involvement/
    .reason for Chain-level introspection tests.

    Using a fake here (rather than a real PlayerEvents class) lets the
    ChainTracker unit tests assert pure chain-boundary logic without any
    stat side effects muddying the assertions.
    """
    def __init__(self, team, quarter=1, ends=False, end_reason="turnover",
                 event_type=None, player=None, is_effective=False,
                 is_score_involvement=False, reason=None):
        self.team = team
        self.quarter = quarter
        self._ends = ends
        self._end_reason = end_reason
        self.event_type = event_type
        self.player = player
        self.is_effective = is_effective
        self.is_score_involvement = is_score_involvement
        self.reason = reason

    def ends_chain(self):
        return self._ends

    @property
    def chain_end_reason(self):
        return self._end_reason
