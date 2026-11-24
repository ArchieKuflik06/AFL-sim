# Tracks chain state and infers restart reasons.
from features.Chain import Chain


class ChainTracker:
    START_REASON_AFTER = {
        "goal": "center_bounce",
        "behind": "kick_in",
        "rushed_behind": "kick_in",
        "turnover": "turnover",
        "possession_change": "turnover",
        "tackle": "stoppage",
        "out_of_bounds": "stoppage",
    }
    DEFAULT_START_REASON = "turnover"

    def __init__(self, on_chain_closed=None):
        self.chains = []
        self.current_chain = None
        self._next_start_reason = "center_bounce"
        self.on_chain_closed = on_chain_closed  # callable(chain) or None

    def process_chain(self, event):
        if self.current_chain is None:
            if event.starts_chain():
                self._start_chain(event)
            else:
                return

        elif self._other_team_has_possession(event) and self._event_changes_possession(event):
            # A mark or turnover by the opposition restarts the chain for the new team.
            self._end_chain("possession_change")
            self._start_chain(event)
            return

        else:
            # Normal play extends the chain until a score or stoppage closes it.
            self.current_chain.add_event(event)

        if event.ends_chain():
            # Goals and behinds close immediately, but may use a special end reason.
            self._end_chain(event.chain_end_reason)

    def _start_chain(self, event):
        self.current_chain = Chain(event.team, event.quarter, event,
                                    start_reason=self._next_start_reason)
        self.current_chain.add_event(event)

    def _event_changes_possession(self, event):
        return event.changes_possession()

    def _end_chain(self, reason):
        chain = self.current_chain
        chain.close(reason)
        self.chains.append(chain)

        self._print_chain_summary(chain)

        self._next_start_reason = self._start_reason_after(reason, chain)
        self.current_chain = None

        if self.on_chain_closed is not None:
            self.on_chain_closed(chain)

    def _print_chain_summary(self, chain):
        team_name = getattr(chain.team, "name", str(chain.team))
        event_types = [getattr(event, "event_type", type(event).__name__) for event in chain.events]
        print(
            f"Chain ended: team={team_name}, quarter={chain.quarter}, "
            f"start_reason={chain.start_reason}, end_reason={chain.end_reason}, "
            f"events={event_types}"
        )

    def _start_reason_after(self, end_reason, chain=None):
        # Match restart position follows the outcome: goal, kick-in, stoppage or turnover.
        if end_reason == "goal":
            return "center_bounce"

        if end_reason == "free_kick" and chain is not None:
            for event in reversed(chain.events):
                if getattr(event, "event_type", None) != "free_kick":
                    continue
                reason = getattr(event, "reason", None)
                # "Lasso" represents insufficient intent or last-disposal rules.
                if getattr(reason, "value", None) == "Lasso":
                    return "turnover"
                return self.DEFAULT_START_REASON

        return self.START_REASON_AFTER.get(end_reason, self.DEFAULT_START_REASON)

    def _other_team_has_possession(self, event):
        return self.current_chain is not None and event.team != self.current_chain.team

    def get_current_chain(self):
        return self.current_chain

    def finalize(self):
        if self.current_chain is not None:
            self._end_chain("end_of_match")