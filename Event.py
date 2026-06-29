from abc import ABC, abstractmethod
from enum import Enum


class FreeKickReason(Enum):
    # Individual High-Frequency Infractions
    HOLDING_BALL = "Holding the Ball"
    HIGH_CONTACT = "High Tackle"
    PUSH_IN_BACK = "Push in the Back"
    HOLDING_MAN = "Holding the Man"
    OUT_ON_FULL = "Out on the Full"
    INSUFFICIENT_INTENT = "Insufficient Intent"  # Standard AFL term for Deliberate Out of Bounds
    
    # Parent Categories (Grouped low-frequency/technical infractions)
    ILLEGAL_CONTACT = "Prohibited Contact"        # Tripping, charging, standard dangerous tackles
    CONTEST_INFRINGEMENT = "Contest Infringement" # Chopping arms, block, ruck/marking interference
    DELAY_OF_GAME = "Delay of Game"               # Time wasting, protected area, stepping over the mark
    TECHNICAL_BREACH = "Technical Breach"         # 6-6-6 formation, illegal interchange, running too far


class Event(ABC):
    """Root abstract class for all match events."""

    def __init__(self, player, time, quarter, team):
        self.player = player
        self.time = time
        self.quarter = quarter
        self.team = team

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
                 distance=None):
        super().__init__(player, time, quarter, team)
        self.is_effective = is_effective
        self.is_contested = is_contested
        self.is_clearance = is_clearance
        self.is_i50 = is_i50
        self.is_rebound50 = is_rebound50
        self.is_turnover = is_turnover
        self.distance = distance

    @property
    @abstractmethod
    def disposal_type(self):
        raise NotImplementedError()

    def apply(self):
        """Apply shared disposal stats."""
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return
        # Use Stats.inc(...) where available to mutate counters consistently
        if self.disposal_type == "kick":
            try:
                stats.inc("kicks")
            except AttributeError:
                pass
        elif self.disposal_type == "handball":
            try:
                stats.inc("handballs")
            except AttributeError:
                pass

        try:
            stats.inc("disposals")
        except AttributeError:
            pass

        for name, active in [("clearances", self.is_clearance),
                             ("i50_entries", self.is_i50),
                             ("rebound_50s", self.is_rebound50),
                             ("contested_disposals", self.is_contested),
                             ("effective_disposals", self.is_effective),
                             ("turnovers", self.is_turnover)]:
            if active:
                try:
                    stats.inc(name)
                except AttributeError:
                    pass

    def display_event(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return

        base = f"{self.disposal_type.title()} #{getattr(stats, self.disposal_type + 's', 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"

        flags = [
            (self.is_effective,  "effective",  "effective_disposals"),
            (self.is_contested,  "contested",  "contested_disposals"),
            (self.is_clearance,  "clearance",  "clearances"),
            (self.is_i50,        "inside 50",  "i50_entries"),
            (self.is_rebound50,  "rebound 50", "rebound_50s"),
            (self.is_turnover,   "turnover",   "turnovers"),
        ]
        details = [
            f"{label} #{getattr(stats, attr, 0)}"
            for active, label, attr in flags if active
        ]

        if self.distance is not None:
            details.append(f"{self.distance}m")

        return f"{base} ({', '.join(details)})" if details else base


class KickEvent(DisposalEvent):
    disposal_type = "kick"

    def __init__(self, player, time, quarter, team,
                 is_effective=False,
                 is_contested=False,
                 is_clearance=False,
                 is_i50=False,
                 is_rebound50=False,
                 is_turnover=False,
                 distance=None):
        super().__init__(player, time, quarter, team,
                         is_effective=is_effective,
                         is_contested=is_contested,
                         is_clearance=is_clearance,
                         is_i50=is_i50,
                         is_rebound50=is_rebound50,
                         is_turnover=is_turnover,
                         distance=distance)

    @property
    def event_type(self):
        return "kick"


class HandballEvent(DisposalEvent):
    disposal_type = "handball"

    def __init__(self, player, time, quarter, team,
                 is_effective=False,
                 is_contested=False,
                 is_clearance=False,
                 is_i50=False,
                 is_rebound50=False,
                 is_turnover=False,
                 distance=None):
        super().__init__(player, time, quarter, team,
                         is_effective=is_effective,
                         is_contested=is_contested,
                         is_clearance=is_clearance,
                         is_i50=is_i50,
                         is_rebound50=is_rebound50,
                         is_turnover=is_turnover,
                         distance=distance)

    @property
    def event_type(self):
        return "handball"
    

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
        self.team.score += self.score_value
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return
        # Use Stats.inc for score counters
        if self.score_type == "goal":
            try:
                stats.inc("goals")
            except AttributeError:
                pass
        elif self.score_type == "behind":
            try:
                stats.inc("behinds")
            except AttributeError:
                pass

    def display_event(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return

        base = f"{self.score_type.title()} #{getattr(stats, self.score_type + 's', 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"

        flags = [
            (self.is_contested,  "contested",  "contested_disposals"),
            (self.is_i50,        "inside 50",  "i50_entries"),
        ]
        details = [
            f"{label} #{getattr(stats, attr, 0)}"
            for active, label, attr in flags if active
        ]

        if self.distance is not None:
            details.append(f"{self.distance}m")

        return f"{base} ({', '.join(details)})" if details else base


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
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return

        # Use Stats.inc for tackles
        try:
            stats.inc("tackles")
        except AttributeError:
            pass

    def display_event(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return

        tackler_name = self.player.name
        tackled_name = getattr(self.tackled_player, "name", "Unknown")
        base = f"Tackle #{getattr(stats, 'tackles', 0)} by {tackler_name} on {tackled_name} at {self.time} mins in Q{self.quarter}"

        return base

    @property
    def event_type(self):
        return "tackle"
    
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
        """Apply shared  mark stats."""
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return

        try:
            stats.inc("marks")
        except AttributeError:
            pass

        for name, active in [("marks_inside_50", self.is_i50),
                             ("marks_contested", self.is_contested),
                             ("marks_intercept", self.is_intercept)]:
            if active:
                try:
                    stats.inc(name)
                except AttributeError:
                    pass

    def display_event(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return

        base = f"Mark #{getattr(stats, 'marks', 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"

        flags = [
            (self.is_contested,  "contested",  "marks_contested"),
            (self.is_i50,        "inside 50",  "marks_inside_50"),
            (self.is_intercept,  "intercept",  "marks_intercept"),
        ]
        details = [
            f"{label} #{getattr(stats, attr, 0)}"
            for active, label, attr in flags if active
        ]

        if self.distance is not None:
            details.append(f"{self.distance}m")

        return f"{base} ({', '.join(details)})" if details else base


    @property
    def event_type(self):
        return "mark"
    
class FreeDisposal(Event):
    """Free kick event: records the player who received the free kick and who committed it."""
    def __init__(self, got_free_kick_player, committed_free_kick_player, time, quarter, team, reason=None):
        super().__init__(got_free_kick_player, time, quarter, team)
        self.committed_free_kick_player = committed_free_kick_player
        self.reason = reason if isinstance(reason, FreeKickReason) else FreeKickReason.PROHIBITED_CONTACT

    def apply(self):
        stats_for = getattr(self.player, "current_game_stats", None)
        stats_against = getattr(self.committed_free_kick_player, "current_game_stats", None)
        if stats_for is None or stats_against is None:
            return

        try:
            stats_for.inc("frees_for")
        except AttributeError:
            pass

        try:
            stats_against.inc("frees_against")
        except AttributeError:
            pass

        # to do: add logic for turnovers only if it's a change in possession
        try:
            stats_against.inc("turnovers")
        except AttributeError:
            pass

    def display_event(self):
        stats_for = getattr(self.player, "current_game_stats", None)
        stats_against = getattr(self.committed_free_kick_player, "current_game_stats", None)
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
    
class Hitout(Event):
    def __init__(self, player, time, quarter, team,
                 is_to_advantage=False,
                 opponent=None):
        super().__init__(player, time, quarter, team)
        self.is_to_advantage = is_to_advantage
        self.opponent = opponent

    def apply(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return
        stats.inc("hitouts")
        if self.is_to_advantage:
            stats.inc("hitouts_to_advantage")

    def display_event(self):
        stats = getattr(self.player, "current_game_stats", None)
        if stats is None:
            return
        base = f"Hitout #{getattr(stats, 'hitouts', 0)} by {self.player.name} at {self.time} mins in Q{self.quarter}"
        if self.is_to_advantage:
            base += f" (to advantage #{getattr(stats, 'hitouts_to_advantage', 0)})"
        return base

    @property
    def event_type(self):
        return "hitout"