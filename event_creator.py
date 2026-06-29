from team import Team
from player import Player
from Event import KickEvent, HandballEvent, GoalEvent, BehindEvent, tackle, Mark, FreeDisposal, Hitout, FreeKickReason
from Match import Match


EVENT_MAP = {
    "goal": GoalEvent,
    "behind": BehindEvent,
    "kick": KickEvent,
    "handball": HandballEvent,
    "mark": Mark,
    "hitout": Hitout,
}


class EventCreater:
    def __init__(self):
        self.home_team = None
        self.away_team = None
        self.match = None
        self.home_players = []
        self.away_players = []

    def build_teams(self):
        self.home_team = Team("Hawthorn Hawks", [], 0)
        self.away_team = Team("Richmond Tigers", [], 0)

        self.home_players = [
            Player("Jack Gunston", 2, "Forward", 80, self.home_team),        
            Player("Lloyd Meek", 21, "Ruck", 75, self.home_team),           
            Player("James Sicily", 4, "Defender", 83, self.home_team),       
            Player("Jai Newcombe", 6, "Midfield", 85, self.home_team),       
            Player("Mitch Lewis", 14, "Forward", 84, self.home_team),        
        ]

        self.away_players = [
            Player("Tom Lynch", 9, "Forward", 84, self.away_team),          
            Player("Toby Nankervis", 17, "Ruck", 78, self.away_team),      
            Player("Dylan Grimes", 8, "Defender", 82, self.away_team),       
            Player("Tim Taranto", 3, "Midfield", 83, self.away_team),      
            Player("Shai Bolton", 7, "Forward", 83, self.away_team),      
        ]

        self.home_team.players = self.home_players
        self.away_team.players = self.away_players

    def build_match(self, venue="MCG"):
        if self.home_team is None or self.away_team is None:
            raise RuntimeError("Teams must be built before creating the match")
        self.match = Match(self.home_team, self.away_team, venue)

    def create_event(self, event_type, player, time, quarter, team, data=None):
        kwargs = data or {}

        if event_type == "tackle":
            tackled = kwargs.get("tackled")
            if tackled is None:
                raise ValueError("Tackle events require 'tackled' player in data")
            return tackle(player, tackled, time, quarter, team)

        if event_type == "free_kick":
            committed = kwargs.get("committed")
            reason = kwargs.get("reason", None)
            if committed is None:
                raise ValueError("Free kick events require 'committed' player in data")
            return FreeDisposal(player, committed, time, quarter, team, reason=reason)

        cls = EVENT_MAP.get(event_type)
        if cls is None:
            raise ValueError(f"Unknown event type: {event_type}")
        return cls(player, time, quarter, team, **kwargs)

    def simulate(self):
        self.build_teams()
        self.build_match()

        event = event_data = [
            # Quarter 1 - Hawks win the tap, clearance chain leads to goal
            ("hitout", self.home_players[1], 0, 1, self.home_team, {"is_to_advantage": True}),
            ("kick", self.home_players[3], 1, 1, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("mark", self.home_players[0], 2, 1, self.home_team, {}),
            ("kick", self.home_players[0], 3, 1, self.home_team, {"is_i50": True, "is_effective": True}),
            ("mark", self.home_players[4], 4, 1, self.home_team, {"is_i50": True}),
            ("goal", self.home_players[4], 5, 1, self.home_team, {"is_i50": True, "is_effective": True}),

            # Tigers win tap, clearance turned over by tackle → holding the ball free
            ("hitout", self.away_players[1], 6, 1, self.away_team, {"is_to_advantage": True}),
            ("kick", self.away_players[3], 7, 1, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.away_players[0], 8, 1, self.away_team, {"is_contested": True, "is_effective": False}),
            ("tackle", self.home_players[3], 9, 1, self.home_team, {"tackled": self.away_players[0], "resulted_in_free": True}),
            ("free_kick", self.home_players[2], 9, 1, self.home_team, {"committed": self.away_players[0], "reason": FreeKickReason.HOLDING_BALL}),
            ("kick", self.home_players[2], 10, 1, self.home_team, {"is_effective": True, "is_i50": True}),
            ("behind", self.home_players[4], 11, 1, self.home_team, {"is_i50": True}),

            # Tigers rebound, intercept mark, kick inside 50, behind
            ("hitout", self.away_players[1], 12, 1, self.away_team, {"is_to_advantage": False}),
            ("kick", self.away_players[2], 13, 1, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("mark", self.away_players[4], 14, 1, self.away_team, {}),
            ("kick", self.away_players[4], 15, 1, self.away_team, {"is_i50": True, "is_effective": True}),
            ("behind", self.away_players[0], 16, 1, self.away_team, {"is_i50": True}),

            # Hawks rebound, chain of handballs, push in back free → goal
            ("kick", self.home_players[2], 17, 1, self.home_team, {"is_rebound50": True, "is_effective": True}),
            ("handball", self.home_players[3], 18, 1, self.home_team, {"is_effective": True}),
            ("handball", self.home_players[0], 19, 1, self.home_team, {"is_effective": True, "is_i50": True}),
            ("free_kick", self.home_players[0], 20, 1, self.home_team, {"committed": self.away_players[2], "reason": FreeKickReason.PUSH_IN_BACK}),
            ("goal", self.home_players[0], 21, 1, self.home_team, {"is_i50": True, "is_effective": True}),

            # Tigers win tap, contested possession chain, high contact free → kick → goal
            ("hitout", self.away_players[1], 22, 1, self.away_team, {"is_to_advantage": True}),
            ("handball", self.away_players[3], 23, 1, self.away_team, {"is_contested": True, "is_effective": True}),
            ("kick", self.away_players[3], 24, 1, self.away_team, {"is_effective": True}),
            ("free_kick", self.away_players[4], 25, 1, self.away_team, {"committed": self.home_players[3], "reason": FreeKickReason.HIGH_CONTACT}),
            ("kick", self.away_players[4], 26, 1, self.away_team, {"is_i50": True, "is_effective": True}),
            ("goal", self.away_players[0], 27, 1, self.away_team, {"is_i50": True, "is_effective": True}),

            # Hawks win tap, turnover, Tigers intercept mark, kick → behind
            ("hitout", self.home_players[1], 28, 1, self.home_team, {"is_to_advantage": False}),
            ("kick", self.home_players[3], 29, 1, self.home_team, {"is_effective": False, "is_turnover": True}),
            ("mark", self.away_players[2], 30, 1, self.away_team, {"is_intercept": True}),
            ("kick", self.away_players[2], 31, 1, self.away_team, {"is_i50": True, "is_effective": True}),
            ("behind", self.away_players[4], 32, 1, self.away_team, {"is_i50": True}),

            # Quarter 2 - Hawks win tap, chain ends in behind
            ("hitout", self.home_players[1], 0, 2, self.home_team, {"is_to_advantage": True}),
            ("kick", self.home_players[3], 1, 2, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.home_players[0], 2, 2, self.home_team, {"is_effective": True}),
            ("kick", self.home_players[4], 3, 2, self.home_team, {"is_i50": True, "is_effective": True}),
            ("mark", self.home_players[0], 4, 2, self.home_team, {"is_i50": True, "is_contested": True}),
            ("behind", self.home_players[0], 5, 2, self.home_team, {"is_i50": True}),

            # Tigers rebound, holding man free → kick → goal
            ("hitout", self.away_players[1], 6, 2, self.away_team, {"is_to_advantage": True}),
            ("kick", self.away_players[3], 7, 2, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("mark", self.away_players[0], 8, 2, self.away_team, {}),
            ("free_kick", self.away_players[0], 9, 2, self.away_team, {"committed": self.home_players[2], "reason": FreeKickReason.HOLDING_MAN}),
            ("kick", self.away_players[0], 10, 2, self.away_team, {"is_i50": True, "is_effective": True}),
            ("goal", self.away_players[4], 11, 2, self.away_team, {"is_i50": True, "is_effective": True}),

            # Hawks win tap, contested clearance, turnover, Tigers score
            ("hitout", self.home_players[1], 12, 2, self.home_team, {"is_to_advantage": False}),
            ("handball", self.home_players[3], 13, 2, self.home_team, {"is_contested": True, "is_effective": False, "is_turnover": True}),
            ("kick", self.away_players[3], 14, 2, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("kick", self.away_players[4], 15, 2, self.away_team, {"is_i50": True, "is_effective": True}),
            ("mark", self.away_players[0], 16, 2, self.away_team, {"is_i50": True}),
            ("goal", self.away_players[0], 17, 2, self.away_team, {"is_i50": True, "is_effective": True}),

            # Hawks chain through midfield, tackle forces holding the ball → goal
            ("hitout", self.home_players[1], 18, 2, self.home_team, {"is_to_advantage": True}),
            ("kick", self.home_players[3], 19, 2, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.home_players[2], 20, 2, self.home_team, {"is_effective": True}),
            ("kick", self.home_players[0], 21, 2, self.home_team, {"is_effective": True}),
            ("handball", self.home_players[4], 22, 2, self.home_team, {"is_contested": True, "is_effective": False}),
            ("tackle", self.away_players[2], 23, 2, self.away_team, {"tackled": self.home_players[4], "resulted_in_free": True}),
            ("free_kick", self.away_players[2], 23, 2, self.away_team, {"committed": self.home_players[4], "reason": FreeKickReason.HOLDING_BALL}),
            ("kick", self.away_players[2], 24, 2, self.away_team, {"is_rebound50": True, "is_effective": True}),
            ("kick", self.home_players[2], 25, 2, self.home_team, {"is_i50": True, "is_effective": True}),
            ("goal", self.home_players[4], 26, 2, self.home_team, {"is_i50": True, "is_effective": True}),

            # Quarter 3 - Tigers win tap, quick goal chain
            ("hitout", self.away_players[1], 0, 3, self.away_team, {"is_to_advantage": True}),
            ("kick", self.away_players[3], 1, 3, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("mark", self.away_players[4], 2, 3, self.away_team, {}),
            ("kick", self.away_players[4], 3, 3, self.away_team, {"is_i50": True, "is_effective": True}),
            ("mark", self.away_players[0], 4, 3, self.away_team, {"is_i50": True}),
            ("goal", self.away_players[0], 5, 3, self.away_team, {"is_i50": True, "is_effective": True}),

            # Hawks rebound chain, holding man free on the mark → behind
            ("hitout", self.home_players[1], 6, 3, self.home_team, {"is_to_advantage": False}),
            ("kick", self.home_players[2], 7, 3, self.home_team, {"is_rebound50": True, "is_effective": True}),
            ("mark", self.home_players[3], 8, 3, self.home_team, {}),
            ("free_kick", self.home_players[3], 9, 3, self.home_team, {"committed": self.away_players[3], "reason": FreeKickReason.HOLDING_MAN}),
            ("kick", self.home_players[3], 10, 3, self.home_team, {"is_i50": True, "is_effective": True}),
            ("behind", self.home_players[0], 11, 3, self.home_team, {"is_i50": True}),

            # Tigers contested chain, intercept mark by Hawks defender, rebound → goal
            ("hitout", self.away_players[1], 12, 3, self.away_team, {"is_to_advantage": True}),
            ("handball", self.away_players[3], 13, 3, self.away_team, {"is_contested": True, "is_effective": True}),
            ("kick", self.away_players[3], 14, 3, self.away_team, {"is_effective": False, "is_turnover": True}),
            ("mark", self.home_players[2], 15, 3, self.home_team, {"is_intercept": True}),
            ("kick", self.home_players[2], 16, 3, self.home_team, {"is_effective": True}),
            ("handball", self.home_players[3], 17, 3, self.home_team, {"is_effective": True}),
            ("kick", self.home_players[0], 18, 3, self.home_team, {"is_i50": True, "is_effective": True}),
            ("goal", self.home_players[4], 19, 3, self.home_team, {"is_i50": True, "is_effective": True}),

            # Tigers push back, tackle forces HTB, kick → goal
            ("hitout", self.away_players[1], 20, 3, self.away_team, {"is_to_advantage": True}),
            ("kick", self.away_players[3], 21, 3, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.away_players[4], 22, 3, self.away_team, {"is_contested": True, "is_effective": False}),
            ("tackle", self.home_players[2], 23, 3, self.home_team, {"tackled": self.away_players[4], "resulted_in_free": True}),
            ("free_kick", self.home_players[2], 23, 3, self.home_team, {"committed": self.away_players[4], "reason": FreeKickReason.HOLDING_BALL}),
            ("kick", self.home_players[2], 24, 3, self.home_team, {"is_effective": True}),
            ("kick", self.home_players[3], 25, 3, self.home_team, {"is_i50": True, "is_effective": True}),
            ("mark", self.home_players[0], 26, 3, self.home_team, {"is_i50": True, "is_contested": True}),
            ("goal", self.home_players[0], 27, 3, self.home_team, {"is_i50": True, "is_effective": True}),

            # Quarter 4 - Tigers win tap, push for comeback
            ("hitout", self.away_players[1], 0, 4, self.away_team, {"is_to_advantage": True}),
            ("kick", self.away_players[3], 1, 4, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.away_players[4], 2, 4, self.away_team, {"is_effective": True}),
            ("kick", self.away_players[0], 3, 4, self.away_team, {"is_i50": True, "is_effective": True}),
            ("mark", self.away_players[4], 4, 4, self.away_team, {"is_i50": True}),
            ("goal", self.away_players[4], 5, 4, self.away_team, {"is_i50": True, "is_effective": True}),

            # Hawks steady, intercept mark, push in back free → goal
            ("hitout", self.home_players[1], 6, 4, self.home_team, {"is_to_advantage": True}),
            ("kick", self.home_players[3], 7, 4, self.home_team, {"is_clearance": True, "is_effective": True}),
            ("mark", self.home_players[2], 8, 4, self.home_team, {"is_intercept": True}),
            ("kick", self.home_players[2], 9, 4, self.home_team, {"is_effective": True}),
            ("handball", self.home_players[3], 10, 4, self.home_team, {"is_effective": True}),
            ("free_kick", self.home_players[4], 11, 4, self.home_team, {"committed": self.away_players[3], "reason": FreeKickReason.PUSH_IN_BACK}),
            ("kick", self.home_players[4], 12, 4, self.home_team, {"is_i50": True, "is_effective": True}),
            ("goal", self.home_players[0], 13, 4, self.home_team, {"is_i50": True, "is_effective": True}),

            # Tigers desperate chain, high contact free → behind
            ("hitout", self.away_players[1], 14, 4, self.away_team, {"is_to_advantage": False}),
            ("kick", self.away_players[3], 15, 4, self.away_team, {"is_clearance": True, "is_effective": True}),
            ("handball", self.away_players[4], 16, 4, self.away_team, {"is_contested": True, "is_effective": True}),
            ("free_kick", self.away_players[0], 17, 4, self.away_team, {"committed": self.home_players[2], "reason": FreeKickReason.HIGH_CONTACT}),
            ("kick", self.away_players[0], 18, 4, self.away_team, {"is_i50": True, "is_effective": True}),
            ("behind", self.away_players[4], 19, 4, self.away_team, {"is_i50": True}),

            # Hawks run out winners, contested chain, holding the ball seals it
            ("hitout", self.home_players[1], 20, 4, self.home_team, {"is_to_advantage": True}),
            ("handball", self.home_players[3], 21, 4, self.home_team, {"is_contested": True, "is_effective": True}),
            ("kick", self.home_players[3], 22, 4, self.home_team, {"is_effective": True}),
            ("handball", self.home_players[0], 23, 4, self.home_team, {"is_effective": True}),
            ("handball", self.away_players[4], 24, 4, self.away_team, {"is_contested": True, "is_effective": False}),
            ("tackle", self.home_players[2], 25, 4, self.home_team, {"tackled": self.away_players[4], "resulted_in_free": True}),
            ("free_kick", self.home_players[2], 25, 4, self.home_team, {"committed": self.away_players[4], "reason": FreeKickReason.HOLDING_BALL}),
            ("kick", self.home_players[2], 26, 4, self.home_team, {"is_i50": True, "is_effective": True}),
            ("goal", self.home_players[4], 27, 4, self.home_team, {"is_i50": True, "is_effective": True}),
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