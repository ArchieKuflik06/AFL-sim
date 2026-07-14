from game_stats.Data_Classes import PlayerStats as Stats, RatingWeightings, FantasyWeightings
class Player:
    def __init__(self, name, number, position, team):
        self.number = number
        self.position = position
        self.name = name
        self.team = team
        self.current_game_stats = Stats()
        self.career_stats = Stats()
        self.weightings = RatingWeightings()
        self.fantasy_weightings = FantasyWeightings()

    def getWeightings(self):
        return self.weightings

    def getFantasyWeightings(self):
        return self.fantasy_weightings

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
    
