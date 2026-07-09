from models.team import Team
'''
to do: post hoc - score involvements, scores
added stat events ground ball gets one percenters
team stats
efficiency stats
'''
class Match:
    def __init__(self, home_team: Team, away_team: Team, venue):
        if not isinstance(home_team, Team):
            raise TypeError("home_team must be a Team")
        if not isinstance(away_team, Team):
            raise TypeError("away_team must be a Team")

        self.home_team = home_team
        self.away_team = away_team
        self.venue = venue
        self.events = []


    def add_event(self, event):
        self.events.append(event)
    

    def remove_event(self, event):
        if event in self.events:
            self.events.remove(event)
        
   

    def display_score(self):
        print(self.home_team.score, self.away_team.score)
        return self.home_team.score, self.away_team.score
    
    def event_review(self, event, overturned=False, new_event_type=None):
        player = event.get_player() if hasattr(event, "get_player") else None
        player_name = getattr(player, "name", None)
        review_result = {
            "event_type": getattr(event, "event_type", None),
            "player": player_name,
            "reviewed": True,
            "overturned": overturned,
            "new_event_type": new_event_type,
        }
        print(f"Review for {player_name}: overturned={overturned}")
        return review_result
    
    def rank_top_scorers(self):
        all_players = self.home_team.players + self.away_team.players
        # Sort players by their fantasy points in descending order
        top_scorers_fantasy = sorted(all_players, key=lambda p: p.current_game_stats.afl_fantasy, reverse=True)
        print("\nTOP 5 SCORERS BY FANTASY POINTS:")
        for player in top_scorers_fantasy[0:5]:
            print(player.name, player.current_game_stats.afl_fantasy)
        print("\nTOP 5 SCORERS BY live ranking")
        top_scorers_live = sorted(all_players, key=lambda p: p.current_game_stats.live_rating, reverse=True)
        for player in top_scorers_live[0:5]:
            print(player.name, player.current_game_stats.live_rating)       
