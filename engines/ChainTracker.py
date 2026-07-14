from features.Chain import Chain

class ChainTracker:
    def __init__(self):
        self.chains = []
        self.current_chain = None
        self.prev_team = None

    def process_chain(self, event):
        if self.current_chain is None:
            self._start_chain(event)
        elif self._other_team_has_possession(event):
            self._end_chain("possession_change")
            self._start_chain(event)
        else:
            self.current_chain.add_event(event)

        self.prev_team = event.team

        if event.ends_chain:
            self._end_chain(self._end_reason(event))

    def _start_chain(self, event):
        self.current_chain = Chain(event.team, event.quarter, event)
        self.current_chain.add_event(event)

    def _end_chain(self, reason):
        self.current_chain.close(reason)
        self.chains.append(self.current_chain)
        self.current_chain = None

    def _other_team_has_possession(self, event):
        # possession changed without an explicit turnover flag
        return self.prev_team is not None and event.team != self.prev_team

    def _end_reason(self, event):
        if event.event_type in ("goal", "behind"):
            return event.event_type
        return "turnover"
    
    def get_current_chain(self):
        return self.current_chain

    def finalize(self):
        if self.current_chain is not None:
            self._end_chain("end_of_match")