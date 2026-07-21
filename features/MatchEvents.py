from abc import ABC, abstractmethod



class MatchEvent(ABC):
    def __init__(self, player, time, quarter, team, event_id=None):
        self.event_id = event_id
        self.player = player
        self.time = time
        self.quarter = quarter
        self.team = team

    @abstractmethod
    def apply(self):
        pass

    @property
    @abstractmethod
    def event_type(self):
        pass

    @abstractmethod
    def display_event(self):
        pass

    def undo(self):
        pass

    def ends_chain(self):
        return False

    @property
    def chain_end_reason(self):
        return "turnover"


class Interchange(MatchEvent):
    def __init__(self, player_off, player_on, time, quarter, team, event_id=None):
        super().__init__(player_on, time, quarter, team, event_id=event_id)
        self.player_off = player_off

    def apply(self):
        self.team.interchange([(self.player_off, self.player)], self.time, self.quarter)

    @property
    def event_type(self):
        return "interchange"

    def display_event(self):
        return f"Interchange: {self.player_off.name} off, {self.player.name} on at {self.time}"


class OutOfBounds(MatchEvent):
    def __init__(self, player, time, quarter, team, event_id=None):
        super().__init__(player, time, quarter, team, event_id=event_id)

    @property
    def event_type(self):
        return "out_of_bounds"

    def apply(self):
        pass

    def undo(self):
        pass

    def display_event(self):
        return f"Out of Bounds: throw in occurred at {self.time} in Q{self.quarter}"


class EventReview(MatchEvent):
    REVIEWABLE_TYPES = ("goal", "behind", "out_of_bounds")

    def __init__(self, match, chain_tracker, player, time, quarter, team,
                 review_of, overturned=False, new_event=None, event_id=None):
        super().__init__(player, time, quarter, team, event_id=event_id)
        self.match = match
        self.chain_tracker = chain_tracker
        self.review_of = review_of
        self.overturned = overturned
        self.new_event = new_event
        self.event = None

    def _resolve_target(self):
        for e in self.match.events:
            if getattr(e, "event_id", None) == self.review_of:
                if e.event_type not in self.REVIEWABLE_TYPES:
                    raise ValueError(f"{e.event_type} events cannot be reviewed")
                return e
        raise ValueError(f"No event found with id {self.review_of}")

    def apply(self):
        self.event = self._resolve_target()
        if self.overturned:
            self.event.undo()
            if self.new_event is not None:
                self.new_event.apply()

    @property
    def event_type(self):
        return "event_review"

    def display_event(self):
        if self.overturned:
            new_desc = self.new_event.event_type if self.new_event else "no result"
            return (f"Event Review: {self.event.event_type} overturned "
                    f"to {new_desc} at {self.event.time} in Q{self.event.quarter}")
        return f"Event Review: {self.event.event_type} upheld at {self.event.time} in Q{self.event.quarter}"