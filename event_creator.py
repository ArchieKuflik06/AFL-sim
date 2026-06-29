from team import Team
from player import Player
from Event import KickEvent, HandballEvent, GoalEvent, BehindEvent
from Match import Match


class EventCreater:
    def __init__(self):
        self.home_team = None
        self.away_team = None
        self.match = None
        self.home_players = []
        self.away_players = []

    def build_teams(self):
        self.home_team = Team("Home Hawks", [], 0)
        self.away_team = Team("Away Tigers", [], 0)

        self.home_players = [
            Player("Alice", 1, "Forward", 80, self.home_team),
            Player("Ben", 2, "Midfield", 75, self.home_team),
            Player("Charlie", 3, "Defender", 78, self.home_team),
        ]

        self.away_players = [
            Player("Dana", 4, "Forward", 82, self.away_team),
            Player("Ethan", 5, "Midfield", 74, self.away_team),
            Player("Fiona", 6, "Defender", 76, self.away_team),
        ]

        self.home_team.players = self.home_players
        self.away_team.players = self.away_players

    def build_match(self, venue="MCG"):
        if self.home_team is None or self.away_team is None:
            raise RuntimeError("Teams must be built before creating the match")

        self.match = Match(self.home_team, self.away_team, venue)

    def create_event(self, event_type, player, time, quarter, team, data=None):
        kwargs = data or {}
        if event_type == "goal":
            return GoalEvent(player, time, quarter, team, **kwargs)
        if event_type == "behind":
            return BehindEvent(player, time, quarter, team, **kwargs)
        if event_type == "kick":
            return KickEvent(player, time, quarter, team, **kwargs)
        if event_type == "handball":
            return HandballEvent(player, time, quarter, team, **kwargs)
        raise ValueError(f"Unknown event type: {event_type}")

    def simulate(self):
        self.build_teams()
        self.build_match()

        event_data = [
            # Quarter 1
            ("kick", self.home_players[0], 1, 1, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.away_players[1], 3, 1, self.away_team, {"is_contested": True, "is_effective": False}),
            ("kick", self.home_players[2], 5, 1, self.home_team, {"is_i50": True, "is_effective": True}),
            ("handball", self.away_players[2], 7, 1, self.away_team, {"is_rebound50": True, "is_effective": True}),
            ("goal", self.home_players[0], 9, 1, self.home_team, {"is_i50": True, "is_effective": True}),
            ("kick", self.away_players[0], 11, 1, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.home_players[1], 13, 1, self.home_team, {"is_contested": True, "is_effective": True}),
            ("behind", self.away_players[2], 15, 1, self.away_team, {"is_i50": True, "is_effective": False}),
            ("kick", self.home_players[2], 17, 1, self.home_team, {"is_rebound50": True, "is_effective": True}),
            ("handball", self.away_players[1], 19, 1, self.away_team, {"is_i50": False, "is_effective": True}),
            # Quarter 2
            ("kick", self.home_players[1], 2, 2, self.home_team, {"is_i50": True, "is_effective": True}),
            ("handball", self.away_players[0], 4, 2, self.away_team, {"is_contested": True, "is_effective": False}),
            ("kick", self.home_players[0], 6, 2, self.home_team, {"is_clearance": True, "is_effective": False}),
            ("goal", self.away_players[2], 8, 2, self.away_team, {"is_i50": True, "is_effective": True}),
            ("handball", self.home_players[2], 10, 2, self.home_team, {"is_rebound50": True, "is_effective": True}),
            ("behind", self.away_players[1], 12, 2, self.away_team, {"is_i50": True, "is_effective": False}),
            ("kick", self.home_players[1], 14, 2, self.home_team, {"is_effective": True}),
            ("handball", self.away_players[0], 16, 2, self.away_team, {"is_contested": False, "is_effective": True}),
            ("kick", self.home_players[0], 18, 2, self.home_team, {"is_rebound50": True, "is_effective": True}),
            ("goal", self.away_players[0], 20, 2, self.away_team, {"is_i50": True, "is_effective": True}),
            # Quarter 3
            ("handball", self.home_players[2], 1, 3, self.home_team, {"is_contested": True, "is_effective": False}),
            ("kick", self.away_players[1], 3, 3, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.home_players[1], 5, 3, self.home_team, {"is_i50": False, "is_effective": True}),
            ("goal", self.home_players[0], 7, 3, self.home_team, {"is_i50": True, "is_effective": True}),
            ("kick", self.away_players[2], 9, 3, self.away_team, {"is_rebound50": True, "is_effective": True}),
            ("behind", self.home_players[2], 11, 3, self.home_team, {"is_i50": True, "is_effective": False}),
            ("handball", self.away_players[0], 13, 3, self.away_team, {"is_effective": True}),
            ("kick", self.home_players[1], 15, 3, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.away_players[1], 17, 3, self.away_team, {"is_contested": True, "is_effective": True}),
            ("goal", self.home_players[2], 19, 3, self.home_team, {"is_i50": True, "is_effective": True}),
            # Quarter 4
            ("kick", self.away_players[0], 2, 4, self.away_team, {"is_effective": True}),
            ("handball", self.home_players[0], 4, 4, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("kick", self.away_players[2], 6, 4, self.away_team, {"is_i50": True, "is_effective": True}),
            ("behind", self.home_players[1], 8, 4, self.home_team, {"is_i50": True, "is_effective": False}),
            ("handball", self.away_players[1], 10, 4, self.away_team, {"is_rebound50": True, "is_effective": True}),
            ("goal", self.home_players[0], 12, 4, self.home_team, {"is_i50": True, "is_effective": True}),
            ("kick", self.away_players[0], 14, 4, self.away_team, {"is_clearance": True, "is_effective": False}),
            ("handball", self.home_players[2], 16, 4, self.home_team, {"is_contested": True, "is_effective": True}),
            ("kick", self.away_players[1], 18, 4, self.away_team, {"is_rebound50": True, "is_effective": True}),
            ("goal", self.home_players[1], 20, 4, self.home_team, {"is_i50": True, "is_effective": True}),
        ]

        events = [self.create_event(*data) for data in event_data]

        for event in events:
            self.match.add_event(event)
            event.apply()
            print(event.display_event())


        print("\nFinal score:")
        home_score, away_score = self.match.display_score()
        print(f"{self.home_team.name}: {home_score}")
        print(f"{self.away_team.name}: {away_score}")

        for player in self.home_players + self.away_players:
            player.display_stats()

        return self.match


if __name__ == "__main__":
    creator = EventCreater()
    creator.simulate()
