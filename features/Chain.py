class Chain:
    def __init__(self, team, quarter, start_event, start_reason=None):
        self.team = team
        self.quarter = quarter
        self.start_event = start_event
        self.start_reason = start_reason
        self.events = []
        self.end_reason = None

    def add_event(self, event):
        self.events.append(event)

    def remove_event(self, event):
        self.events.remove(event)

    def close(self, end_reason):
        self.end_reason = end_reason

    def resulted_in_score(self):
        return self.end_reason in ("goal", "behind")

    def scored_from_turnover(self):
        return self.start_reason == "turnover" and self.resulted_in_score()

    def points_scored(self):
        if not self.resulted_in_score():
            return 0
        return 6 if self.end_reason == "goal" else 1

    def _find_score_event_index(self):
        for index, event in enumerate(self.events):
            if getattr(event, "event_type", None) in {"goal", "behind", "rushed_behind"}:
                return index
        return None

    def get_score_involvement_players(self):
        if not self.resulted_in_score():
            return []

        players = []
        for event in self.events:
            if getattr(event, "is_score_involvement", False):
                players.append(event.player)

        if players:
            return list(dict.fromkeys(players))

        score_event_index = self._find_score_event_index()
        if score_event_index is None:
            return []

        for event in self.events[:score_event_index]:
            if getattr(event, "event_type", None) in {"kick", "handball"} and getattr(event, "is_effective", False):
                players.append(event.player)

        if players:
            return list(dict.fromkeys(players))

        scorer = self.events[score_event_index].player if score_event_index is not None else None
        if scorer is not None:
            return [scorer]

        return []

    def get_goal_assist_players(self):
        if not self.resulted_in_score() or self.end_reason != "goal":
            return []

        score_event_index = self._find_score_event_index()
        if score_event_index is None:
            return []

        for event in reversed(self.events[:score_event_index]):
            if getattr(event, "event_type", None) in {"kick", "handball"} and getattr(event, "is_effective", False):
                return [event.player]

        return []