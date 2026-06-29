from team import Team

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
        self.current_quarter = 1
        self.time = 0

    def add_event(self, event):
        self.events.append(event)
        self.update_score(event)

    def remove_event(self, event):
        if event in self.events:
            self.events.remove(event)
        
    def update_score(self, event):
        if event.event_type == "goal":
            event.team.score += 6
        elif event.event_type == "behind":
            event.team.score += 1
    

    def display_score(self):
        print(self.home_team.score, self.away_team.score)
        return self.home_team.score, self.away_team.score
    