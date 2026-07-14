from features.team import Team

class TeamBuilder:
    def __init__(self, name):
        self.name = name
        self.starting_players = []
        self.bench_players = []

    def add_starting_player(self, player):
        self.starting_players.append(player)

    def add_bench_player(self, player):
        self.bench_players.append(player)

    def build(self):
        team = Team(
            self.name,
            self.starting_players,
            self.bench_players,
            0
        )

        # assign team reference to players
        for player in team.players:
            player.team = team

        return team