from builders.MatchBuilder import MatchBuilder
from builders.TeamBuilder import TeamBuilder
from engines.EventProcessor import EventProcessor
from engines.EventLoader import EventLoader
from features.player import Player
from engines.ChainTracker import ChainTracker
from features.MatchEvents import EventReview


class MatchEngine:

    def __init__(self):
        self.match = None
        self.event_processor = None

    

    def create_match(self):
        home_team = self.create_home_team()
        away_team = self.create_away_team()

        match_builder = MatchBuilder()
        self.match = match_builder.build(home_team, away_team, "MCG")

        self.event_processor = EventProcessor(self.match)
        self.chain_tracker = ChainTracker()
        self.event_engine = EventLoader(self.match, self.chain_tracker)
      

        self.chain_tracker = ChainTracker()

        return self.match


    def create_home_team(self):

        builder = TeamBuilder("Hawthorn Hawks")

        builder.starting_players = [
            Player("Jack Gunston", 2, "Forward", None),
            Player("Lloyd Meek", 21, "Ruck", None),
            Player("James Sicily", 4, "Defender", None),
            Player("Jai Newcombe", 6, "Midfield", None),
            Player("Mitch Lewis", 14, "Forward", None),
        ]

        builder.bench_players = [
            Player("Will Day", 1, "Defender", None),
            Player("James Worpel", 5, "Midfield", None),
        ]
    
        return builder.build()


    def create_away_team(self):

        builder = TeamBuilder("Richmond Tigers")

        builder.starting_players = [
            Player("Tom Lynch", 9, "Forward", None),
            Player("Toby Nankervis", 17, "Ruck", None),
            Player("Dylan Grimes", 8, "Defender", None),
            Player("Tim Taranto", 3, "Midfield", None),
            Player("Shai Bolton", 7, "Forward", None),
        ]

        builder.bench_players = [
            Player("Jack Riewoldt", 4, "Forward", None),
            Player("David Astbury", 6, "Defender", None),
        ]

        return builder.build()
    
    def run(self, raw_events):

        events = [self.event_engine.load_event(d) for d in raw_events]
        events.sort(key=lambda e: (e.quarter, e.time))

        for event in events:
           #event.player.display_stats()
            self.event_processor.process(event)
            self.chain_tracker.process_chain(event)

    
        self.chain_tracker.finalize()
        return self.match 

    def review_event(self, target_time, target_quarter, overturned=False, new_event=None):
        target_event = next(
            e for e in self.match.events
            if e.time == target_time and e.quarter == target_quarter
        )
        review = EventReview(target_event, self.chain_tracker, overturned=overturned, new_event=new_event)
        self.event_processor.process(review)
        return review    




        