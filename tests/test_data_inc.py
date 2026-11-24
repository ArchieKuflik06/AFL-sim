# Regression tests for stat increments on player and team events.
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features.PlayerEvents import (
    KickEvent,
    HandballEvent,
    GoalEvent,
    BehindEvent,
    Mark,
    FreeDisposal,
    Hitout,
    Spoil,
    GroundBallGet,
    OnePercenter,
    KnockOns,
)
from features.player import Player
from features.team import Team
from game_stats.Data_Classes import BaseStats, PlayerStats


class TestDataInc(unittest.TestCase):
    def setUp(self):
        self.player = Player("Test Player", 1, "Midfield", None)
        self.team = Team("Test Team", [self.player], [], 0)
        self.player.team = self.team

    def test_base_stats_inc_updates_stat_value(self):
        stats = BaseStats()
        stats.inc("kicks", 3)
        self.assertEqual(stats.kicks, 3)
        stats.inc("kicks")
        self.assertEqual(stats.kicks, 4)

    def test_base_stats_inc_raises_for_unknown_stat(self):
        stats = BaseStats()
        with self.assertRaises(AttributeError):
            stats.inc("unknown_stat")

    def test_base_stats_inc_set_amount_updates_time_on_ground(self):
        stats = PlayerStats()
        stats.inc_set_amount("time_on_ground_minutes", 5)
        self.assertEqual(stats.time_on_ground_minutes, 5)

    def test_base_stats_set_amount_assigns_value(self):
        stats = BaseStats()
        stats.set_amount("marks", 7)
        self.assertEqual(stats.marks, 7)

    def test_kick_event_apply_increments_shared_disposal_stats(self):
        event = KickEvent(
            self.player,
            10,
            1,
            self.team,
            is_effective=True,
            is_contested=True,
            is_clearance=True,
            is_i50=True,
            is_rebound50=True,
            is_turnover=True,
            is_clanger=True,
        )
        event.apply()

        self.assertEqual(self.player.current_game_stats.disposals, 1)
        self.assertEqual(self.team.current_game_stats.disposals, 1)
        self.assertEqual(self.player.current_game_stats.kicks, 1)
        self.assertEqual(self.team.current_game_stats.kicks, 1)
        self.assertEqual(self.player.current_game_stats.effective_disposals, 1)
        self.assertEqual(self.player.current_game_stats.contested_disposals, 1)
        self.assertEqual(self.player.current_game_stats.clearances, 1)
        self.assertEqual(self.player.current_game_stats.i50_entries, 1)
        self.assertEqual(self.player.current_game_stats.rebound_50s, 1)
        self.assertEqual(self.player.current_game_stats.turnovers, 1)
        self.assertEqual(self.player.current_game_stats.clangers, 1)
        self.assertEqual(self.team.current_game_stats.clangers, 1)

    def test_handball_event_apply_increments_shared_handball_stats(self):
        event = HandballEvent(
            self.player,
            10,
            1,
            self.team,
            is_effective=True,
            is_contested=True,
            is_clearance=True,
            is_i50=True,
            is_rebound50=True,
            is_turnover=True,
            is_clanger=True,
        )
        event.apply()

        self.assertEqual(self.player.current_game_stats.disposals, 1)
        self.assertEqual(self.team.current_game_stats.disposals, 1)
        self.assertEqual(self.player.current_game_stats.handballs, 1)
        self.assertEqual(self.team.current_game_stats.handballs, 1)
        self.assertEqual(self.player.current_game_stats.effective_disposals, 1)
        self.assertEqual(self.player.current_game_stats.contested_disposals, 1)
        self.assertEqual(self.player.current_game_stats.clearances, 1)
        self.assertEqual(self.player.current_game_stats.i50_entries, 1)
        self.assertEqual(self.player.current_game_stats.rebound_50s, 1)
        self.assertEqual(self.player.current_game_stats.turnovers, 1)
        self.assertEqual(self.player.current_game_stats.clangers, 1)

    def test_goal_event_apply_increments_score_and_shared_stats(self):
        event = GoalEvent(self.player, 10, 1, self.team, is_i50=True, is_contested=True)
        event.apply()

        self.assertEqual(self.team.score, 6)
        self.assertEqual(self.player.current_game_stats.goals, 1)
        self.assertEqual(self.team.current_game_stats.goals, 1)
        self.assertEqual(self.player.current_game_stats.disposals, 1)
        self.assertEqual(self.player.current_game_stats.kicks, 1)
        self.assertEqual(self.player.current_game_stats.i50_entries, 1)
        self.assertEqual(self.player.current_game_stats.contested_disposals, 1)

    def test_behind_event_apply_increments_score_and_shared_stats(self):
        event = BehindEvent(self.player, 10, 1, self.team, is_i50=True, is_contested=True)
        event.apply()

        self.assertEqual(self.team.score, 1)
        self.assertEqual(self.player.current_game_stats.behinds, 1)
        self.assertEqual(self.team.current_game_stats.behinds, 1)
        self.assertEqual(self.player.current_game_stats.disposals, 1)
        self.assertEqual(self.player.current_game_stats.kicks, 1)
        self.assertEqual(self.player.current_game_stats.i50_entries, 1)
        self.assertEqual(self.player.current_game_stats.contested_disposals, 1)

    def test_mark_event_apply_increments_mark_stats(self):
        event = Mark(
            self.player,
            10,
            1,
            self.team,
            is_i50=True,
            is_contested=True,
            is_intercept=True,
        )
        event.apply()

        self.assertEqual(self.player.current_game_stats.marks, 1)
        self.assertEqual(self.team.current_game_stats.marks, 1)
        self.assertEqual(self.player.current_game_stats.marks_inside_50, 1)
        self.assertEqual(self.player.current_game_stats.marks_contested, 1)
        self.assertEqual(self.player.current_game_stats.marks_intercept, 1)

    def test_free_disposal_apply_increments_free_kick_stats(self):
        opponent = Player("Opponent", 2, "Defender", None)
        opponent.team = self.team
        event = FreeDisposal(self.player, opponent, 10, 1, self.team)
        event.apply()

        self.assertEqual(self.player.current_game_stats.frees_for, 1)
        self.assertEqual(self.team.current_game_stats.frees_for, 1)
        self.assertEqual(opponent.current_game_stats.frees_against, 1)

    def test_hitout_apply_increments_hitout_stats(self):
        event = Hitout(self.player, 10, 1, self.team, is_to_advantage=True)
        event.apply()

        self.assertEqual(self.player.current_game_stats.hitouts, 1)
        self.assertEqual(self.team.current_game_stats.hitouts, 1)
        self.assertEqual(self.player.current_game_stats.hitouts_to_advantage, 1)
        self.assertEqual(self.team.current_game_stats.hitouts_to_advantage, 1)

    def test_spoil_apply_increments_spoils(self):
        event = Spoil(self.player, 10, 1, self.team)
        event.apply()

        self.assertEqual(self.player.current_game_stats.spoils, 1)
        self.assertEqual(self.team.current_game_stats.spoils, 1)

    def test_ground_ball_get_apply_increments_ground_ball_gets(self):
        event = GroundBallGet(self.player, 10, 1, self.team)
        event.apply()

        self.assertEqual(self.player.current_game_stats.ground_ball_gets, 1)
        self.assertEqual(self.team.current_game_stats.ground_ball_gets, 1)

    def test_one_percenter_apply_increments_one_percenters(self):
        event = OnePercenter(self.player, 10, 1, self.team)
        event.apply()

        self.assertEqual(self.player.current_game_stats.one_percenters, 1)
        self.assertEqual(self.team.current_game_stats.one_percenters, 1)

    def test_knock_ons_apply_increments_knock_ons(self):
        event = KnockOns(self.player, 10, 1, self.team)
        event.apply()

        self.assertEqual(self.player.current_game_stats.knock_ons, 1)
        self.assertEqual(self.team.current_game_stats.knock_ons, 1)


if __name__ == "__main__":
    unittest.main()
