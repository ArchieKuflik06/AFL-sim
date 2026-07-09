class EventProcessor:

    def __init__(self, match):
        self.match = match
        self.current_quarter = 1
        self.current_time = 0

    def process(self, event):

        # Update match state
        self.current_quarter = event.quarter
        self.current_time = event.time

        # Store event
        self.match.add_event(event)

        # Apply game logic
        event.apply()
        
        if hasattr(event, "apply_fantasy"):
            event.apply_fantasy()


    def get_events(self):
        return self.match.events

    def get_match_clock(self):
        return self.current_quarter, self.current_time