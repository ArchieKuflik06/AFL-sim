from models.Match import Match

class MatchBuilder:

    def __init__(self):
        pass

    def build(self, home_team, away_team, venue):
        return Match(
            home_team,
            away_team,
            venue
        )