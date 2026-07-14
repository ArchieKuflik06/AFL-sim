from features.team import Team
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
               
    def get_team(self, name):
        if self.home_team.name == name:
            return self.home_team
        if self.away_team.name == name:
            return self.away_team
        raise ValueError(f"Team '{name}' not found in this match")

    def get_player(self, name):
        for team in (self.home_team, self.away_team):
            for player in team.players:
                if player.name == name:
                    return player
        raise ValueError(f"Player '{name}' not found in this match")