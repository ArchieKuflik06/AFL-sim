
from builders.MatchBuilder import MatchBuilder
from builders.TeamBuilder import TeamBuilder
from engines.EventProcessor import EventProcessor
from engines.EventLoader import EventLoader
from engines.ChainTracker import ChainTracker
from game_stats.TeamStats import CalcTeamStats
from features import Match, player
from features.player import Player
from features.MatchEvents import EventReview


class MatchEngine:

    def __init__(self):
        self.match = None
        self.event_processor = None
        self.chain_tracker = None
        self.home_stats_calc = None
        self.away_stats_calc = None

    def create_match(self):
        home_team = self.create_home_team()
        away_team = self.create_away_team()

        match_builder = MatchBuilder()
        self.match = match_builder.build(home_team, away_team, "MCG")

        # One CalcTeamStats per team, shared between EventProcessor (clock-driven
        # stats) and MatchEngine's chain-closed dispatch (chain-driven stats).
        self.home_stats_calc = CalcTeamStats(home_team, home_team.current_game_stats)
        self.away_stats_calc = CalcTeamStats(away_team, away_team.current_game_stats)

        # Single ChainTracker instance, owned here, shared with EventLoader.
        self.chain_tracker = ChainTracker(on_chain_closed=self._dispatch_chain_closed)
        self.event_engine = EventLoader(self.match, self.chain_tracker)

        self.event_processor = EventProcessor(
            self.match,
            team_stats_calcs=(self.home_stats_calc, self.away_stats_calc),
        )

        return self.match

    def _dispatch_chain_closed(self, chain):
        self.home_stats_calc.on_chain_closed(chain)
        self.away_stats_calc.on_chain_closed(chain)

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
            self.event_processor.process(event)
            self.chain_tracker.process_chain(event)

        self.chain_tracker.finalize()

        for player in self.match.home_team.on_ground:
            player.display_stats()
        for player in self.match.away_team.on_ground:
            player.display_stats()

        for team in [self.match.home_team, self.match.away_team]:
            team.display_stats()

        self.match.rank_top_scorers()
        return self.match

    def review_event(self, target_time, target_quarter, overturned=False, new_event=None):
        target_event = next(
            e for e in self.match.events
            if e.time == target_time and e.quarter == target_quarter
        )
        review = EventReview(target_event, self.chain_tracker, overturned=overturned, new_event=new_event)
        self.event_processor.process(review)
        return review