from dataclasses import dataclass, asdict


@dataclass
class Stats:
    kicks: int = 0
    handballs: int = 0
    disposals: int = 0
    goals: int = 0
    behinds: int = 0
    tackles: int = 0
    spoils: int = 0
    marks: int = 0
    turnovers_forced: int = 0
    turnovers_conceded: int = 0
    clearances: int = 0
    i50_entries: int = 0
    rebound_50s: int = 0
    contested_disposals: int = 0
    effective_disposals: int = 0
    rating_delta: float = 0.0

    def inc(self, name: str, amount: int = 1):
        if not hasattr(self, name):
            raise AttributeError(f"Unknown stat: {name}")
        setattr(self, name, getattr(self, name) + amount)

    def to_dict(self):
        return asdict(self)


class Player:
    def __init__(self, name, number, position, rating, team):
        self.number = number
        self.position = position
        self.rating = rating
        self.name = name
        self.team = team
        self.current_game_stats = Stats()
        self.career_stats = Stats()

    def reset_game_stats(self):
        self.current_game_stats = Stats()

    def display_stats(self):
        print(f"{self.name} stats:", self.current_game_stats.to_dict())
        print("\n")

    def getName(self):
        print(self.name)
        return self.name
    
    def getTeam(self):
        print(self.team)
        return self.team
    
    def getPosition(self):
        print(self.position)
        return self.position
    
    def getRating(self):
        print(self.rating)
        return self.rating
    
    def calcRating(self, eventRating):
        self.rating += eventRating
