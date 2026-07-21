import time as time_module
from features.MatchEvents import EventReview


class EventProcessor:

    def __init__(self, match, team_stats_calcs=(), playback_speed=1.0, debug=True):
        """
        playback_speed: multiplier on real time.
            1.0  = true real-time (1 game-minute = 60 real seconds)
            2.0  = twice as fast (1 game-minute = 30 real seconds)
            0.1  = slow motion
        debug: if True, skips all sleeping and prints instantly.
        team_stats_calcs: tuple of (home_stats_calc, away_stats_calc), each a
            CalcTeamStats instance. Shared with MatchEngine so both the clock
            (here) and chain closures (there) can feed the same aggregators.
        """
        self.match = match
        self.current_quarter = 1
        self.current_time = 0
        self.playback_speed = playback_speed
        self.debug = debug
        self._last_time = 0
        self._last_quarter = 1
        self.tog_tracker = TOGTracker()

        self.home_stats_calc, self.away_stats_calc = team_stats_calcs

    def process(self, event):
        is_review = isinstance(event, EventReview)

        if not is_review:
            # Detect quarter change and reset the clock baseline
            if event.quarter != self._last_quarter:
                self._last_time = 0
                self._last_quarter = event.quarter

            delta_minutes = event.time - self._last_time

            # Real-time playback: sleep unless in debug mode
            if delta_minutes > 0 and not self.debug:
                delta_seconds = (delta_minutes * 60) / self.playback_speed
                time_module.sleep(delta_seconds)

            self.current_quarter = event.quarter
            self.current_time = event.time

            # Time-on-ground only accrues for real, time-advancing events
            self.tog_tracker.update(self.match, delta_minutes)

            # Time-winning accrues off the score state heading into this event
            home_score = self.match.home_team.score
            away_score = self.match.away_team.score
            self.home_stats_calc.calculate_time_winning(home_score > away_score, delta_minutes)
            self.away_stats_calc.calculate_time_winning(away_score > home_score, delta_minutes)

            self._last_time = event.time

            # Reviews aren't part of the played event log
            self.match.add_event(event)

        event.apply()
        if hasattr(event, "apply_fantasy"):
            event.apply_fantasy()

        line = event.display_event()
        if line:
            print(line)

    def get_events(self):
        return self.match.events

    def get_match_clock(self):
        return self.current_quarter, self.current_time


class TOGTracker:
    def update(self, match, delta_minutes):
        for team in (match.home_team, match.away_team):
            for player in team.on_ground:
                player.current_game_stats.inc_set_amount("time_on_ground_minutes", amount=delta_minutes)