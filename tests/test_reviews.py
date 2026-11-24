# Regression tests for review events and score rewrites.
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features.Match import Match
from features.PlayerEvents import GoalEvent, BehindEvent, Mark, FreeDisposal, FreeKickReason, Tackle, KickEvent
from features.MatchEvents import EventReview, OutOfBounds
from features.player import Player
from features.team import Team


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.home_player = Player("Home Player", 1, "Forward", None)
        self.away_player = Player("Away Player", 2, "Midfield", None)

        self.home_team = Team("Home", [self.home_player], [], 0)
        self.away_team = Team("Away", [self.away_player], [], 0)

        self.home_player.team = self.home_team
        self.away_player.team = self.away_team

        self.match = Match(self.home_team, self.away_team, "MCG")

    def apply_and_register(self, event):
        self.match.add_event(event)
        event.apply()

    def test_reviewability_is_defined_per_event_type(self):
        goal_event = GoalEvent(self.home_player, 10, 1, self.home_team)
        behind_event = BehindEvent(self.home_player, 10, 1, self.home_team)
        mark_event = Mark(self.home_player, 10, 1, self.home_team)
        tackle_event = Tackle(self.home_player, self.away_player, 10, 1, self.home_team)
        out_of_bounds = OutOfBounds(self.home_player, 10, 1, self.home_team)

        assert goal_event.is_reviewable()
        assert behind_event.is_reviewable()
        assert mark_event.is_reviewable()
        assert out_of_bounds.is_reviewable()
        assert not tackle_event.is_reviewable()

    def test_chain_end_reason_is_defined_by_the_event(self):
        goal_event = GoalEvent(self.home_player, 10, 1, self.home_team)
        kick_event = KickEvent(self.home_player, 10, 1, self.home_team)

        assert goal_event.ends_chain()
        assert goal_event.chain_end_reason == "goal"
        assert not kick_event.ends_chain()

    def test_point_review_to_goal(self):
        point_event = BehindEvent(self.home_player, 10, 1, self.home_team, event_id=1)
        self.apply_and_register(point_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=1,
            overturned=True,
            new_event=GoalEvent(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 6)
        self.assertEqual(self.home_player.current_game_stats.behinds, 0)
        self.assertEqual(self.home_player.current_game_stats.goals, 1)
        self.assertEqual(self.home_player.current_game_stats.disposals, 1)

    def test_goal_review_to_point(self):
        goal_event = GoalEvent(self.home_player, 10, 1, self.home_team, event_id=2)
        self.apply_and_register(goal_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=2,
            overturned=True,
            new_event=BehindEvent(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 1)
        self.assertEqual(self.home_player.current_game_stats.goals, 0)
        self.assertEqual(self.home_player.current_game_stats.behinds, 1)
        self.assertEqual(self.home_player.current_game_stats.disposals, 1)

    def test_point_review_to_point(self):
        first_point = BehindEvent(self.home_player, 10, 1, self.home_team, event_id=3)
        self.apply_and_register(first_point)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=3,
            overturned=True,
            new_event=BehindEvent(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 1)
        self.assertEqual(self.home_player.current_game_stats.behinds, 1)
        self.assertEqual(self.home_player.current_game_stats.disposals, 1)

    def test_goal_review_to_goal(self):
        first_scorer = Player("First Scorer", 3, "Forward", None)
        second_scorer = Player("Second Scorer", 4, "Forward", None)
        self.home_team.players.extend([first_scorer, second_scorer])
        self.home_team.on_ground.add(first_scorer)
        self.home_team.on_ground.add(second_scorer)
        first_scorer.team = self.home_team
        second_scorer.team = self.home_team

        goal_event = GoalEvent(first_scorer, 10, 1, self.home_team, event_id=4)
        self.apply_and_register(goal_event)

        review = EventReview(
            self.match,
            None,
            second_scorer,
            11,
            1,
            self.home_team,
            review_of=4,
            overturned=True,
            new_event=GoalEvent(second_scorer, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 6)
        self.assertEqual(first_scorer.current_game_stats.goals, 0)
        self.assertEqual(second_scorer.current_game_stats.goals, 1)
        self.assertEqual(second_scorer.current_game_stats.disposals, 1)

    def test_point_review_to_mark(self):
        behind_event = BehindEvent(self.home_player, 10, 1, self.home_team, event_id=5)
        self.apply_and_register(behind_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=5,
            overturned=True,
            new_event=Mark(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 0)
        self.assertEqual(self.home_player.current_game_stats.behinds, 0)
        self.assertEqual(self.home_player.current_game_stats.marks, 1)

    def test_mark_review_to_point(self):
        mark_event = Mark(self.home_player, 10, 1, self.home_team, event_id=6)
        self.apply_and_register(mark_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=6,
            overturned=True,
            new_event=BehindEvent(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 1)
        self.assertEqual(self.home_player.current_game_stats.marks, 0)
        self.assertEqual(self.home_player.current_game_stats.behinds, 1)
        self.assertEqual(self.home_player.current_game_stats.disposals, 1)

    def test_goal_review_to_mark(self):
        goal_event = GoalEvent(self.home_player, 10, 1, self.home_team, event_id=7)
        self.apply_and_register(goal_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=7,
            overturned=True,
            new_event=Mark(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 0)
        self.assertEqual(self.home_player.current_game_stats.goals, 0)
        self.assertEqual(self.home_player.current_game_stats.marks, 1)

    def test_mark_review_to_goal(self):
        mark_event = Mark(self.home_player, 10, 1, self.home_team, event_id=8)
        self.apply_and_register(mark_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=8,
            overturned=True,
            new_event=GoalEvent(self.home_player, 11, 1, self.home_team),
        )
        review.apply()

        self.assertEqual(self.home_team.score, 6)
        self.assertEqual(self.home_player.current_game_stats.marks, 0)
        self.assertEqual(self.home_player.current_game_stats.goals, 1)

    def test_goal_review_to_no_score(self):
        goal_event = GoalEvent(self.home_player, 10, 1, self.home_team, event_id=9)
        self.apply_and_register(goal_event)

        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=9,
            overturned=True,
            new_event=None,
        )
        review.apply()

        self.assertEqual(self.home_team.score, 0)
        self.assertEqual(self.home_player.current_game_stats.goals, 0)

    def test_point_review_to_out_on_the_full(self):
        behind_event = BehindEvent(self.home_player, 10, 1, self.home_team, event_id=10)
        self.apply_and_register(behind_event)

        free_kick = FreeDisposal(
            self.home_player,
            self.away_player,
            11,
            1,
            self.home_team,
            reason=FreeKickReason.OUT_ON_FULL,
        )
        review = EventReview(
            self.match,
            None,
            self.home_player,
            11,
            1,
            self.home_team,
            review_of=10,
            overturned=True,
            new_event=free_kick,
        )
        review.apply()

        self.assertEqual(self.home_team.score, 0)
        self.assertEqual(self.home_player.current_game_stats.behinds, 0)
        self.assertEqual(self.home_player.current_game_stats.frees_for, 1)
        self.assertEqual(self.away_player.current_game_stats.frees_against, 1)


if __name__ == "__main__":
    unittest.main()
