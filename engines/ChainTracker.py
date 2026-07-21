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
        self.prev_team = None
        self._next_start_reason = "center_bounce"
        self.on_chain_closed = on_chain_closed  # callable(chain) or None

    def process_chain(self, event):
        if self.current_chain is None:
            self._start_chain(event)
        elif self._other_team_has_possession(event):
            self._end_chain("possession_change")
            self._start_chain(event)
        else:
            self.current_chain.add_event(event)

        self.prev_team = event.team

        if event.ends_chain():
            self._end_chain(event.chain_end_reason)

    def _start_chain(self, event):
        self.current_chain = Chain(event.team, event.quarter, event,
                                    start_reason=self._next_start_reason)
        self.current_chain.add_event(event)

    def _end_chain(self, reason):
        chain = self.current_chain
        chain.close(reason)
        self.chains.append(chain)

        self._next_start_reason = self._start_reason_after(reason, chain)
        self.current_chain = None

        if self.on_chain_closed is not None:
            self.on_chain_closed(chain)

    def _start_reason_after(self, end_reason, chain=None):
        if end_reason in {"goal", "behind", "rushed_behind"}:
            return "center_bounce"

        if end_reason in {"out_of_bounds", "tackle"}:
            return "stoppage"

        if end_reason == "free_kick" and chain is not None:
            for event in reversed(chain.events):
                if getattr(event, "event_type", None) != "free_kick":
                    continue
                reason = getattr(event, "reason", None)
                if getattr(reason, "value", None) == "Lasso":
                    return "stoppage"
                return self.DEFAULT_START_REASON

        return self.START_REASON_AFTER.get(end_reason, self.DEFAULT_START_REASON)

    def _infer_start_reason(self, chain):
        if chain is None:
            return self.DEFAULT_START_REASON

        if chain.end_reason in {"goal", "behind", "rushed_behind"}:
            return "center_bounce"

        if chain.end_reason in {"out_of_bounds", "tackle"}:
            return "stoppage"

        if not chain.events:
            return chain.start_reason or self.DEFAULT_START_REASON

        for event in reversed(chain.events):
            event_type = getattr(event, "event_type", None)
            if event_type == "out_of_bounds":
                return "stoppage"
            if event_type == "tackle":
                return "stoppage"
            if event_type == "free_kick":
                reason = getattr(event, "reason", None)
                if getattr(reason, "value", None) == "Lasso":
                    return "stoppage"
                break

        return chain.start_reason or self.DEFAULT_START_REASON

    def _other_team_has_possession(self, event):
        return self.prev_team is not None and event.team != self.prev_team

    def get_current_chain(self):
        return self.current_chain

    def finalize(self):
        if self.current_chain is not None:
            self._end_chain("end_of_match")