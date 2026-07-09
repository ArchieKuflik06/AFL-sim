from abc import ABC, abstractmethod
from enum import Enum

from Data_Classes import raw_to_rating
import models.team as team


class FreeKickReason(Enum):
    # Individual High-Frequency Infractions
    HOLDING_BALL = "Holding the Ball"
    HIGH_CONTACT = "High Tackle"
    PUSH_IN_BACK = "Push in the Back"
    HOLDING_MAN = "Holding the Man"
    OUT_ON_FULL = "Out on the Full"
    INSUFFICIENT_INTENT = "Insufficient Intent"  
    
    # Parent Categories (Grouped low-frequency/technical infractions)
    ILLEGAL_CONTACT = "Prohibited Contact"       
    CONTEST_INFRINGEMENT = "Contest Infringement" 
    DELAY_OF_GAME = "Delay of Game"               
    TECHNICAL_BREACH = "Technical Breach"     


class Event(ABC):
    """Root abstract class for all match events."""

    def __init__(self, player, time, quarter, team):
        self.player = player
        self.time = time
        self.quarter = quarter
        self.team = team

    def get_player(self):
        return self.player
    
    def player_stats(self):
        return getattr(self.player, "current_game_stats", None)

    def team_stats(self):
        return getattr(self.team, "current_game_stats", None)

    def _get_stats_for(self, entity):
        return getattr(entity, "current_game_stats", None)

    def _get_player_stats(self):
        return self.player_stats()
    
    def _increment_stats(self, entity, *stat_names):
        #given stats names increments the stat for the given entity
        stats = self._get_stats_for(entity)
        if stats is None:
            return None
        for stat_name in stat_names:
            stats.inc(stat_name)
        return stats

    def _increment_shared_stats(self, *stat_names):
        #increments the given stats for both the player and the team
        self._increment_stats(self.player, *stat_names)
        self._increment_stats(self.team, *stat_names)

    def _increment_team_stats(self, *stat_names):
        return self._increment_stats(self.team, *stat_names)
    
    def _apply_to_player_and_team(self, player, team, *stat_names):
        self._increment_stats(player, *stat_names)
        self._increment_stats(team, *stat_names)

    def _increment_player_rating(self, player, *stat_names):
        stats = self._get_stats_for(player)
        if stats is None:
            return None
        for stat_name in stat_names:
            stats.inc_rating(player.getWeightings().get_weight(stat_name))
        if hasattr(player, "current_game_stats"):
            player.rating = stats.live_rating
        return stats

    def _increment_player_fantasy(self, player, weight_key, count=1):
        stats = self._get_stats_for(player)
        if stats is None:
            return None
        weight = player.getFantasyWeightings().get_weight(weight_key)
        stats.inc_fantasy(int(weight * count))
        return stats

    def _format_base_event(self, label, counter_attr, stats=None):
        if stats is None:
            stats = self._get_player_stats()
        if stats is None:
            return None
        return f"{label} #{getattr(stats, counter_attr, 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"

    def _format_flagged_message(self, base, stats, flags, distance=None):
        if stats is None:
            return None

        details = [
            f"{label} #{getattr(stats, attr, 0)}"
            for active, label, attr in flags if active
        ]

        if distance is not None:
            details.append(f"{distance}m")

        return f"{base} ({', '.join(details)})" if details else base

    @property
    @abstractmethod
    def event_type(self):
        raise NotImplementedError()

    @abstractmethod
    def apply(self):
        """Apply this event to player/team state."""
        raise NotImplementedError()

    @abstractmethod
    def display_event(self):
        raise NotImplementedError()


class DisposalEvent(Event, ABC):
    """Abstract base for all disposals: kicks and handballs."""

    def __init__(self, player, time, quarter, team,
                 is_effective=False,
                 is_contested=False,
                 is_clearance=False,
                 is_i50=False,
                 is_rebound50=False,
                 is_turnover=False,
                 is_clanger=False,
                 is_score_involvement=False,
                 is_goal_assist=False,
                 distance=None):
        super().__init__(player, time, quarter, team)
        self.is_effective = is_effective
        self.is_contested = is_contested
        self.is_clearance = is_clearance
        self.is_i50 = is_i50
        self.is_rebound50 = is_rebound50
        self.is_turnover = is_turnover
        self.is_clanger = is_clanger
        self.is_score_involvement = is_score_involvement
        self.is_goal_assist = is_goal_assist
        self.distance = distance

    @property
    @abstractmethod
    def disposal_type(self):
        raise NotImplementedError()

    def apply(self):
        """Apply shared disposal stats to both player and team totals."""
        self._increment_shared_stats("disposals")

        if self.disposal_type == "kick":
            self._increment_shared_stats("kicks")
            self._increment_player_rating(self.player, "kicks")
        elif self.disposal_type == "handball":
            self._increment_shared_stats("handballs")
            self._increment_player_rating(self.player, "handballs")

        for name, active in [("clearances", self.is_clearance),
                             ("i50_entries", self.is_i50),
                             ("rebound_50s", self.is_rebound50),
                             ("contested_disposals", self.is_contested),
                             ("effective_disposals", self.is_effective),
                             ("turnovers", self.is_turnover),
                             ("clangers", self.is_clanger)]:
            if active:
                self._increment_shared_stats(name)
                self._increment_player_rating(self.player, name)

    def display_event(self):
        stats = self._get_player_stats()
        if stats is None:
            return

        base = self._format_base_event(self.disposal_type.title(), self.disposal_type + "s", stats=stats)
        flags = [
            (self.is_effective,  "effective",  "effective_disposals"),
            (self.is_contested,  "contested",  "contested_disposals"),
            (self.is_clearance,  "clearance",  "clearances"),
            (self.is_i50,        "inside 50",  "i50_entries"),
            (self.is_rebound50,  "rebound 50", "rebound_50s"),
            (self.is_turnover,   "turnover",   "turnovers"),
            (self.is_clanger,    "clanger",    "clangers"),
        ]
        return self._format_flagged_message(base, stats, flags, distance=self.distance)


class KickEvent(DisposalEvent):
    disposal_type = "kick"
    #to do :ensure effective disposal are counted correctly in terms of turnovers and clangers

    def __init__(self, player, time, quarter, team,
is_effective=False,
                 is_contested=False,
                 is_clearance=False,
                 is_i50=False,
                 is_rebound50=False,
                 is_turnover=False,
                 is_clanger=False,
                 is_score_involvement=False,
                 is_goal_assist=False,
                 distance=None):
        super().__init__(player, time, quarter, team,
                         is_effective=is_effective,
                         is_contested=is_contested,
                         is_clearance=is_clearance,
                         is_i50=is_i50,
                         is_rebound50=is_rebound50,
                         is_turnover=is_turnover,
                         is_clanger=is_clanger,
                         is_score_involvement=is_score_involvement,
                         is_goal_assist=is_goal_assist,
                         distance=distance)

    @property
    def event_type(self):
        return "kick"
    
    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "kick")


class HandballEvent(DisposalEvent):
    disposal_type = "handball"

    def __init__(self, player, time, quarter, team,
is_effective=False,
                 is_contested=False,
                 is_clearance=False,
                 is_i50=False,
                 is_rebound50=False,
                 is_turnover=False,
                 is_clanger=False,
                 is_score_involvement=False,
                 is_goal_assist=False,
                 distance=None):
        super().__init__(player, time, quarter, team,
                         is_effective=is_effective,
                         is_contested=is_contested,
                         is_clearance=is_clearance,
                         is_i50=is_i50,
                         is_rebound50=is_rebound50,
                         is_turnover=is_turnover,
                         is_clanger=is_clanger,
                         is_score_involvement=is_score_involvement,
                         is_goal_assist=is_goal_assist,
                         distance=distance)

    @property
    def event_type(self):
        return "handball"
    
    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "handball")
    

class ScoreEvent(KickEvent, ABC):
    """Abstract score event for goals and behinds."""
    #to do implement rushed behinds when starting to do team stats

    @property
    @abstractmethod
    def score_type(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def score_value(self):
        raise NotImplementedError()
    
    def apply(self):
        super().apply()
        if self.score_type == "goal":
            self._increment_shared_stats("goals")
            self._increment_player_rating(self.player, "goals")
            self.team.score += self.score_value
        elif self.score_type == "behind":
            self._increment_shared_stats("behinds")
            self._increment_player_rating(self.player, "behinds")
            self.team.score += self.score_value

    def display_event(self):
        stats = self._get_player_stats()
        if stats is None:
            return

        base = self._format_base_event(self.score_type.title(), self.score_type + "s", stats=stats)
        flags = [
            (self.is_contested,  "contested",  "contested_disposals"),
            (self.is_i50,        "inside 50",  "i50_entries"),
        ]
        return self._format_flagged_message(base, stats, flags, distance=self.distance)

    def apply_fantasy(self):
        # Apply underlying disposal fantasy and then add the score bonus.
        try:
            super().apply_fantasy()
        except Exception:
            pass
        self._increment_player_fantasy(self.player, self.score_type)


class GoalEvent(ScoreEvent):
    @property
    def event_type(self):
        return "goal"

    @property
    def score_type(self):
        return "goal"

    @property
    def score_value(self):
        return 6
    

class BehindEvent(ScoreEvent):
    @property
    def event_type(self):
        return "behind"

    @property
    def score_type(self):
        return "behind"

    @property
    def score_value(self):
        return 1
    

class tackle(Event):
    """Tackle event: records the tackler and the tackled player."""
    def __init__(self, tackler, tackled_player, time, quarter, team):
        super().__init__(tackler, time, quarter, team)
        self.tackled_player = tackled_player

    def apply(self):
        self._increment_shared_stats("tackles")
        self._increment_player_rating(self.player, "tackles")

    def display_event(self):
        stats = self._get_player_stats()
        if stats is None:
            return

        tackler_name = self.player.name
        tackled_name = getattr(self.tackled_player, "name", "Unknown")
        return f"Tackle #{getattr(stats, 'tackles', 0)} by {tackler_name} on {tackled_name} at {self.time} mins in Q{self.quarter}"

    @property
    def event_type(self):
        return "tackle"
    
    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "tackle")

class Mark(Event):
    """Mark event: records the player who took the mark."""
    def __init__(self, player, time, quarter, team,
                 is_i50=False,
                 is_contested=False,
                 is_intercept=False,
                 distance=None):
        super().__init__(player, time, quarter, team)
        self.is_i50 = is_i50
        self.is_contested = is_contested
        self.is_intercept = is_intercept
        self.distance = distance

    def apply(self):
        """Apply shared mark stats to both player and team totals."""
        self._increment_shared_stats("marks")
        self._increment_player_rating(self.player, "marks")

        for name, active in [("marks_inside_50", self.is_i50),
                             ("marks_contested", self.is_contested),
                             ("marks_intercept", self.is_intercept)]:
            if active:
                self._increment_shared_stats(name)
                self._increment_player_rating(self.player, name)

    def display_event(self):
        stats = self._get_player_stats()
        if stats is None:
            return

        base = self._format_base_event("Mark", "marks", stats=stats)
        flags = [
            (self.is_contested,  "contested",  "marks_contested"),
            (self.is_i50,        "inside 50",  "marks_inside_50"),
            (self.is_intercept,  "intercept",  "marks_intercept"),
        ]
        return self._format_flagged_message(base, stats, flags, distance=self.distance)


    @property
    def event_type(self):
        return "mark"
    
    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "mark")

class FreeDisposal(Event):
    """Free kick event: records the player who received the free kick and who committed it."""
    def __init__(self, got_free_kick_player, committed_free_kick_player, time, quarter, team, reason=None):
        super().__init__(got_free_kick_player, time, quarter, team)
        self.committed_free_kick_player = committed_free_kick_player
        self.reason = reason if isinstance(reason, FreeKickReason) else FreeKickReason.ILLEGAL_CONTACT

    def apply(self):
        self._increment_shared_stats("frees_for")
        self._increment_player_rating(self.player, "frees_for")
        self._apply_to_player_and_team(
            self.committed_free_kick_player,
            getattr(self.committed_free_kick_player, "team", None),
            "frees_against",
            "turnovers",
        )
        self._increment_player_rating(self.committed_free_kick_player, "frees_against", "turnovers")

    def display_event(self):
        stats_for = self._get_stats_for(self.player)
        stats_against = self._get_stats_for(self.committed_free_kick_player)
        if stats_for is None or stats_against is None:
            return

        reason_str = f" ({self.reason.value})" if self.reason else ""
        return (
            f"Free Kick #{getattr(stats_for, 'frees_for', 0)} to {self.player.name}"
            f" by {self.committed_free_kick_player.name} #{getattr(stats_against, 'frees_against', 0)}"
            f"{reason_str} at {self.time} mins in Q{self.quarter}"
        )
    @property
    def event_type(self):
        return "free_kick"
    
    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "free_for")
        self._increment_player_fantasy(self.committed_free_kick_player, "free_against")

class Hitout(Event):
    def __init__(self, player, time, quarter, team,
                 is_to_advantage=False,
                 opponent=None):
        super().__init__(player, time, quarter, team)
        self.is_to_advantage = is_to_advantage
        self.opponent = opponent

    def apply(self):
        self._increment_shared_stats("hitouts")
        self._increment_player_rating(self.player, "hitouts")
        if self.is_to_advantage:
            self._increment_shared_stats("hitouts_to_advantage")
            self._increment_player_rating(self.player, "hitouts_to_advantage")

    def display_event(self):
        stats = self._get_player_stats()
        if stats is None:
            return
        base = f"Hitout #{getattr(stats, 'hitouts', 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"
        if self.is_to_advantage:
            base += f" (to advantage #{getattr(stats, 'hitouts_to_advantage', 0)})"
        return base

    @property
    def event_type(self):
        return "hitout"
    
    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "hitout")

class Spoil(Event):
    def __init__(self, player, time, quarter, team):
        super().__init__(player, time, quarter, team)


    def apply(self):
        self._increment_shared_stats("spoils")
        self._increment_player_rating(self.player, "spoils")

    def apply_fantasy(self):
        self._increment_player_fantasy(self.player, "spoil")

    def display_event(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return
        return f"Spoil #{getattr(stats, 'spoils', 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"

    @property
    def event_type(self):
        return "spoil"
    

    