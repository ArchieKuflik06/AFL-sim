from abc import ABC, abstractmethod


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
                 distance=None):
        super().__init__(player, time, quarter, team)
        self.is_effective = is_effective
        self.is_contested = is_contested
        self.is_clearance = is_clearance
        self.is_i50 = is_i50
        self.is_rebound50 = is_rebound50
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

        if self.disposal_type == "kick":
            stats.kicks += 1
        elif self.disposal_type == "handball":
            stats.handballs += 1

        stats.disposals += 1

        if self.is_clearance and hasattr(stats, "clearances"):
            stats.clearances += 1
        if self.is_i50 and hasattr(stats, "i50_entries"):
            stats.i50_entries += 1
        if self.is_rebound50 and hasattr(stats, "rebound_50s"):
            stats.rebound_50s += 1
        if self.is_contested and hasattr(stats, "contested_disposals"):
            stats.contested_disposals += 1
        if self.is_effective and hasattr(stats, "effective_disposals"):
            stats.effective_disposals += 1

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
                 distance=None):
        super().__init__(player, time, quarter, team,
                         is_effective=is_effective,
                         is_contested=is_contested,
                         is_clearance=is_clearance,
                         is_i50=is_i50,
                         is_rebound50=is_rebound50,
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
                 distance=None):
        super().__init__(player, time, quarter, team,
                         is_effective=is_effective,
                         is_contested=is_contested,
                         is_clearance=is_clearance,
                         is_i50=is_i50,
                         is_rebound50=is_rebound50,
                         distance=distance)

    @property
    def event_type(self):
        return "handball"
    

class ScoreEvent(KickEvent, ABC):
    """Abstract score event for goals and behinds."""

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

        if self.score_type == "goal" and hasattr(stats, "goals"):
            stats.goals += 1
        elif self.score_type == "behind" and hasattr(stats, "behinds"):
            stats.behinds += 1

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
    
