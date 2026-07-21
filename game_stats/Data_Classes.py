from dataclasses import dataclass, asdict

RAW_RATING_FLOOR = -5.0
RAW_RATING_CEILING = 35.0
RATING_EXPONENT = 0.6


def raw_to_rating(raw: float, floor: float = RAW_RATING_FLOOR, ceiling: float = RAW_RATING_CEILING, exponent: float = RATING_EXPONENT) -> float:
    clamped = max(raw, floor)
    shifted = clamped - floor
    ceiling_shifted = ceiling - floor
    linear = min(shifted / ceiling_shifted, 1.0)
    return round((linear ** exponent) * 10, 2)


@dataclass
class BaseStats:
    #stats shared by players and teams
    kicks: int = 0
    handballs: int = 0
    disposals: int = 0
    goals: int = 0
    goal_assists: int = 0
    score_involvements: int = 0
    behinds: int = 0
    tackles: int = 0
    spoils: int = 0
    marks: int = 0
    marks_inside_50: int = 0
    marks_contested: int = 0
    marks_intercept: int = 0
    turnovers: int = 0
    turnovers_forced: int = 0
    clangers: int = 0
    turnovers_conceded: int = 0
    clearances: int = 0
    i50_entries: int = 0
    rebound_50s: int = 0
    contested_disposals: int = 0
    effective_disposals: int = 0
    frees_for: int = 0
    frees_against: int = 0
    hitouts: int = 0
    hitouts_to_advantage: int = 0
    disposal_efficiency: float = 0.0
    goal_accuracy: float = 0.0
    one_percenters: int = 0
    ground_ball_gets: int = 0
    knock_ons: int = 0



    def inc(self, name: str, amount: int = 1):
        if not hasattr(self, name):
            raise AttributeError(f"Unknown stat: {name}")
        setattr(self, name, getattr(self, name) + amount)

    def inc_set_amount(self, name: str, amount: int = 1):
        if not hasattr(self, name):
            raise AttributeError(f"Unknown stat: {name}")
        setattr(self, name, getattr(self, name) + amount)

    def set_amount(self, name: str, amount: int):
        if not hasattr(self, name):
            raise AttributeError(f"Unknown stat: {name}")
        setattr(self, name, amount)

    def calc_disposal_efficiency(self):
        if self.disposals > 0:
            self.disposal_efficiency = round((self.effective_disposals / self.disposals) * 100, 2)
        else:
            self.disposal_efficiency = 0.0

    def calc_goal_accuracy(self):
        if (self.goals + self.behinds) > 0:
            self.goal_accuracy = round((self.goals / (self.goals + self.behinds)) * 100, 2)
        else:
            self.goal_accuracy = 0.0

    def to_dict(self):
        return asdict(self)
    
@dataclass
class RatingWeightings:
    kicks: float = 0.01
    handballs: float = 0.05
    disposals: float = 0.0
    goals: float = 3.500
    goal_assists: float = 1.000
    score_involvements: float = 0.0
    behinds: float = 1.000
    tackles: float = 0.250
    spoils: float = 0.500
    marks: float = 0.167
    marks_inside_50: float = 1.000
    marks_contested: float = 1.000
    marks_intercept: float = 1.000
    turnovers: float = 0.0
    turnovers_forced: float = 0.0
    clangers: float = -0.250
    turnovers_conceded: float = 0.0
    clearances: float = 0.333
    i50_entries: float = 0.333
    rebound_50s: float = 0.333
    contested_disposals: float = 0.125
    effective_disposals: float = 0.067
    frees_for: float = 1.000
    frees_against: float = -1.000
    hitouts: float = 0.056
    hitouts_to_advantage: float = 0.200
    one_percenters: float = 0.333
    ground_ball_gets: float = 0.200
    knock_ons: float = 0.00

    def to_dict(self):
        return asdict(self)
    
    def get_weight(self, stat_name: str) -> float:
        if not hasattr(self, stat_name):
            raise AttributeError(f"Unknown stat: {stat_name}")
        return getattr(self, stat_name)

@dataclass
class FantasyWeightings:
    kick: float = 3.0
    handball: float = 2.0
    goal: float = 6.0
    behind: float = 1.0
    mark: float = 3.0
    tackle: float = 4.0
    free_for: float = 1.0
    free_against: float = -3.0
    hitout: float = 1.0

    def to_dict(self):
        return asdict(self)
    
    def get_weight(self, stat_name: str) -> float:
        if not hasattr(self, stat_name):
            raise AttributeError(f"Unknown fantasy stat: {stat_name}")
        return getattr(self, stat_name)

@dataclass    
class PlayerStats(BaseStats):
    """Player-only counters."""
    rating_delta: float = 0.0
    live_rating: float = 0.0
    afl_fantasy: int = 0
    time_on_ground_minutes: float = 0.0

    def inc_fantasy(self, amount: int):
        # `afl_fantasy` is a numeric attribute on this dataclass; update it directly
        if not hasattr(self, "afl_fantasy"):
            raise AttributeError("PlayerStats has no attribute 'afl_fantasy'")
        self.afl_fantasy = getattr(self, "afl_fantasy") + amount

    def update_live_rating(self):
        self.live_rating = raw_to_rating(self.rating_delta)

    def inc_rating(self, delta: float):
        self.rating_delta += delta
        self.update_live_rating()


@dataclass
class TeamStats(BaseStats):
    """Team-only counters."""
    inside_50s_scored_from: int = 0
    points_from_turnovers: int = 0
    time_winning: int = 0
    rushed_behinds: int = 0
    points_from_kick_ins: int = 0
    points_from_stoppage: int = 0
    points_from_center_bounces: int = 0

    def calc_i50s_scored_from(self):
        if self.i50_entries > 0:
            self.inside_50s_scored_from = round((self.goals + self.behinds) / self.i50_entries * 100, 2)
        else:
            self.inside_50s_scored_from = 0.0


    