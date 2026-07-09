import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_creator import EventCreater
from models.Match import Match
from models.player import Player
from models.team import Team


class DummyEvent:
    def __init__(self, event_type, player_name):
        self.event_type = event_type
        self.player = type("P", (), {"name": player_name})()

    def get_player(self):
        return self.player


class TeamAndReviewTests(unittest.TestCase):
    def test_build_teams_uses_on_ground_and_off_ground_players(self):
        creator = EventCreater()
        creator.build_teams()

        self.assertEqual(len(creator.home_team.on_ground), len(creator.home_players))
        self.assertEqual(creator.home_team.off_ground, set())
        self.assertEqual(creator.home_team.players, creator.home_players)

        self.assertEqual(len(creator.away_team.on_ground), len(creator.away_players))
        self.assertEqual(creator.away_team.off_ground, set())
        self.assertEqual(creator.away_team.players, creator.away_players)

    def test_interchange_updates_ground_sets_and_log(self):
        player_on = Player("On Player", 1, "Midfield", 80, None)
        player_off = Player("Off Player", 2, "Forward", 78, None)
        team = Team("Test Team", [player_on], [], 0)

        team.interchange([(player_on, player_off)], 5, 1)

        self.assertIn(player_off, team.on_ground)
        self.assertIn(player_on, team.off_ground)
        self.assertNotIn(player_on, team.on_ground)
        self.assertEqual(len(team.interchange_log), 1)
        self.assertEqual(team.interchange_log[0]["time"], 5)
        self.assertEqual(team.interchange_log[0]["quarter"], 1)

    def test_event_review_returns_a_review_result(self):
        home_team = Team("Home", [], [], 0)
        away_team = Team("Away", [], [], 0)
        match = Match(home_team, away_team, "MCG")
        event = DummyEvent("goal", "Test Player")

        result = match.event_review(event, overturned=True)

        self.assertEqual(result["event_type"], "goal")
        self.assertEqual(result["player"], "Test Player")
        self.assertTrue(result["reviewed"])
        self.assertTrue(result["overturned"])


if __name__ == "__main__":
    unittest.main()
