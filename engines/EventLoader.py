from features.PlayerEvents import (
    BehindEvent, FreeDisposal, GoalEvent, HandballEvent, Hitout, KickEvent,
    Mark, Tackle, FreeKickReason, GroundBallGet, OnePercenter, KnockOns,
)
from features.MatchEvents import Interchange, OutOfBounds, EventReview

class EventLoader:

    CLASS_MAP = {
        "kick": KickEvent, "handball": HandballEvent,
        "goal": GoalEvent, "behind": BehindEvent,
        "mark": Mark, "hitout": Hitout,
        "tackle": Tackle, "free_kick": FreeDisposal,
        "ground_ball_get": GroundBallGet,
        "one_percenter": OnePercenter,
        "knock_on": KnockOns,
        "interchange": Interchange,
        "out_of_bounds": OutOfBounds,
    }
    PLAYER_FIELDS = {"player", "tackler", "tackled_player",
                     "got_free_kick_player", "committed_free_kick_player",
                     "player_off", "player_on"}

    def __init__(self, match, chain_tracker):
        self.match = match
        self.chain_tracker = chain_tracker

    def load_event(self, d):
        d = dict(d)
        event_type = d.pop("event_type")
        event_id = d.pop("event_id", d.pop("id", None))

        if event_type == "event_review":
            d["event_id"] = event_id
            return self._load_review(d)

        cls = self.CLASS_MAP[event_type]
        d["team"] = self.match.get_team(d["team"])
        for field in self.PLAYER_FIELDS & d.keys():
            d[field] = self.match.get_player(d[field])
        if "reason" in d:
            d["reason"] = FreeKickReason[d["reason"]]
        if event_id is not None:
            d["event_id"] = event_id  
        return cls(**d)

    def _load_review(self, d):
        new_event_dict = d.pop("new_event", None)
        new_event = self.load_event(new_event_dict) if new_event_dict else None

        return EventReview(
            match=self.match,
            chain_tracker=self.chain_tracker,
            player=self.match.get_player(d["player"]),
            time=d["time"],
            quarter=d["quarter"],
            team=self.match.get_team(d["team"]),
            review_of=d["review_of"],
            overturned=d.get("overturned", False),
            new_event=new_event,
            event_id=d.get("event_id"),
        )