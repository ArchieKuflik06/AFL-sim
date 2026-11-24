# Quick script to sanity-check chain-rule behaviour.
from features.Chain import Chain
from features.PlayerEvents import GoalEvent, Tackle
from features.MatchEvents import OutOfBounds
from game_stats.Data_Classes import TeamStats, PlayerStats
from game_stats.TeamStats import CalcTeamStats
from engines.ChainTracker import ChainTracker

class DummyPlayer:
    def __init__(self, name='player'):
        self.name = name

class DummyTeam:
    def __init__(self, name='team'):
        self.name = name
        self.score = 0

# Goal chain -> center bounce
team = DummyTeam('home')
player = DummyPlayer('scorer')
player.current_game_stats = PlayerStats()
team_stats = TeamStats()
team.current_game_stats = team_stats
chain = Chain(team, 1, GoalEvent(player, 10, 1, team), start_reason='turnover')
chain.add_event(GoalEvent(player, 10, 1, team))
chain.end_reason = 'goal'
CalcTeamStats(team, team_stats).on_chain_closed(chain)
print('center_bounce_points', team_stats.points_from_center_bounces)

# Out of bounds chain -> stoppage
team2 = DummyTeam('away')
player2 = DummyPlayer('player2')
chain2 = Chain(team2, 1, OutOfBounds(player2, 10, 1, team2), start_reason='turnover')
chain2.add_event(OutOfBounds(player2, 10, 1, team2))
chain2.end_reason = 'out_of_bounds'
team_stats2 = TeamStats()
team2.current_game_stats = team_stats2
CalcTeamStats(team2, team_stats2).on_chain_closed(chain2)
print('stoppage_from_out_of_bounds', team_stats2.points_from_stoppage)

# Tackle chain -> stoppage
team3 = DummyTeam('home')
tackler = DummyPlayer('tackler')
tackled = DummyPlayer('tackled')
chain3 = Chain(team3, 1, Tackle(tackler, tackled, 10, 1, team3), start_reason='turnover')
chain3.add_event(Tackle(tackler, tackled, 10, 1, team3))
chain3.end_reason = 'tackle'
team_stats3 = TeamStats()
team3.current_game_stats = team_stats3
CalcTeamStats(team3, team_stats3).on_chain_closed(chain3)
print('stoppage_from_tackle', team_stats3.points_from_stoppage)

tracker = ChainTracker()
print('infer_out_of_bounds', tracker._infer_start_reason(chain2))
print('infer_tackle', tracker._infer_start_reason(chain3))
