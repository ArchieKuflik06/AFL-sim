from game_stats.Data_Classes import TeamStats as Stats

class Team:
    def __init__(self, name, players_starting_on, players_starting_off, score):
        self.name = name
        self.players = players_starting_on + players_starting_off
        self.score = score
        self.on_ground = set(players_starting_on)
        self.off_ground = set(players_starting_off)
        self.interchange_log = []
        self.current_game_stats = Stats()

    def interchange(self, swaps, time, quarter):
        """
        adds to a list of players being swapped on and off the ground, and updates the on_ground set accordingly
        swaps: list of (player_off, player_on) tuples
        """
        for player_off, player_on in swaps:
            if player_off not in self.on_ground:
                raise ValueError(f"{player_off.name} is not currently on the ground")
            if player_on in self.on_ground:
                raise ValueError(f"{player_on.name} is already on the ground")

            self.on_ground.discard(player_off)
            self.on_ground.add(player_on)
            self.off_ground.discard(player_on)
            self.off_ground.add(player_off)

            self.interchange_log.append({
                "player_off": player_off,
                "player_on": player_on,
                "time": time,
                "quarter": quarter,
            })
    
    def getScore(self):
        print(self.score)
        return self.score
    
    def display_stats(self):
        print(f"{self.name} stats:", self.current_game_stats.to_dict())
        print("\n")


    def display_on_ground_players(self):
        print(f"{self.name} on ground players:", [player.name for player in self.on_ground])
        return [player.name for player in self.on_ground]
    
    def display_off_ground_players(self):
        print(f"{self.name} off ground players:", [player.name for player in self.off_ground])
        return [player.name for player in self.off_ground]
    
    def getName(self):
        print(self.name)
        return self.name
    
    def getPlayers(self):
        print(self.players)
        return self.players
    
    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player
        raise ValueError(f"Player '{name}' not found on {self.name}")