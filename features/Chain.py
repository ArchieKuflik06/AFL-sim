class Chain:
    def __init__(self, team, quarter, start_event):
        self.team = team
        self.quarter = quarter
        self.start_event = start_event
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def remove_event(self, event):
        self.events.remove(event)

    def close(self, end_reason):
        self.end_reason = end_reason

    def resulted_in_score(self):
        return self.end_reason in ("goal", "behind")
    
    def resulted_in_score(self):
        return self.end_reason in ("goal", "behind")

    def get_score_involvement_players(self):
        if not self.resulted_in_score():
            return []

        disposals = [e for e in self.events if e.event_type in ("kick", "handball")]
        players = [d.player for d in disposals]

        return list(dict.fromkeys(players))