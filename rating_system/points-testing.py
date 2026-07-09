import pandas as pd
import numpy as np
from pathlib import Path

#try to find the best weighting system taking in positional context to later use on game bases


csv_path = Path(__file__).resolve().parent / "afl_stats_2024.csv"
df = pd.read_csv(csv_path)
df = df.rename(columns={
    "player.player.position": "position",
    "clearances.totalClearances": "clearances",
    "extendedStats.effectiveDisposals": "effective_disposals",
    "extendedStats.hitoutsToAdvantage": "hitouts_to_advantage",
    "extendedStats.interceptMarks": "intercept_marks",
    "extendedStats.spoils": "spoils",
    "extendedStats.groundBallGets": "ground_ball_gets",
    "marksInside50": "marks_inside_50",
    "contestedMarks": "contested_marks",
    "contestedPossessions": "contested_possessions",
    "freesFor": "frees_for",
    "freesAgainst": "frees_against",
    "rebound50s": "rebound_50s",
    "inside50s": "inside_50s",
    "goalAssists": "goal_assists",
    "onePercenters": "one_percenters",
    "dreamTeamPoints": "dream_team_points",
    "player.player.player.givenName": "first_name",
    "player.player.player.surname": "last_name",
})
df["player_name"] = df["first_name"] + " " + df["last_name"]

position_map = {
    "C": "Midfielder", "WL": "Midfielder", "WR": "Midfielder",
    "RR": "Midfielder", "R": "Midfielder",
    "CHF": "Forward", "FF": "Forward", "FPL": "Forward",
    "FPR": "Forward", "HFFL": "Forward", "HFFR": "Forward",
    "CHB": "Defender", "FB": "Defender", "BPL": "Defender",
    "BPR": "Defender", "HBFL": "Defender", "HBFR": "Defender",
    "RK": "Ruck",
    "INT": "Interchange", "SUB": "Interchange", "EMERG": "Interchange",
}
df["position_group"] = df["position"].map(position_map).fillna("Unknown")
df_active = df[~df["position_group"].isin(["Interchange", "Unknown"])].copy()

# Current weights from analysis. All tracked stats are represented here.
# `disposals` is deliberately zero, because kicks and handballs are already weighted.
WEIGHTS = {
    "kicks":               0.077,
    "handballs":           0.111,
    "disposals":           0.0,
    "goals":               3.500,
    "goal_assists":        1.000,
    "score_involvements":  0.0,
    "behinds":             1.000,
    "tackles":             0.250,
    "spoils":              0.500,
    "marks":               0.167,
    "marks_inside_50":     1.000,
    "marks_contested":     1.000,
    "marks_intercept":     1.000,
    "turnovers":          -0.500,
    "turnovers_forced":    0.250,
    "clangers":           -0.250,
    "turnovers_conceded": -0.500,
    "clearances":          0.333,
    "i50_entries":         0.333,
    "rebound_50s":         0.333,
    "contested_disposals": 0.125,
    "effective_disposals": 0.067,
    "frees_for":           1.000,
    "frees_against":      -1.000,
    "hitouts":             0.056,
    "hitouts_to_advantage": 0.200,
    "disposal_efficiency": 0.0,
    "goal_accuracy":       0.0,
    "ground_ball_gets":    0.200,
    "one_percenters":      0.333,
    "intercept_marks":     1.000,
}

def compute_raw(row, goal_weight):
    score = 0.0
    for stat, w in WEIGHTS.items():
        score += row.get(stat, 0) * w
    score += row.get("goals", 0) * goal_weight
    return score

# Test goal weights from 1.0 to 3.5
goal_weights_to_test = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]

# Normalisation curve — same as RatingEngine
RAW_CEILING = 35.0
RAW_FLOOR   = -5.0
DEFAULT_GOAL_WEIGHT = 2.5
PERCENTILE_RATING_EXPONENT = 2.2

# Legacy normalisation curve path. The new percentile rating engine is the preferred method.
def normalise(raw):
    clamped = max(RAW_FLOOR, raw)
    shifted = clamped - RAW_FLOOR
    ceiling_shifted = RAW_CEILING - RAW_FLOOR
    linear = min(shifted / ceiling_shifted, 1.0)
    curved = linear ** 0.6
    return round(curved * 10, 2)

# Convert a percentile into a 0-10 rating where 10 is possible but reserved for the true outliers.
def percentile_to_rating(percentile, exponent=PERCENTILE_RATING_EXPONENT):
    pct = max(0.0, min(100.0, percentile))
    return round(10.0 * (pct / 100.0) ** exponent, 2)

print("HOW GOAL WEIGHT AFFECTS RATINGS FOR KEY GAME TYPES")
print("=" * 70)

test_games = {
    "Average game (15 disp, 1 goal, 4 marks, 2 tackles)": {
        "kicks": 9, "handballs": 6, "marks": 4, "goals": 1,
        "tackles": 2, "clearances": 1, "inside_50s": 2,
        "effective_disposals": 10, "clangers": 2,
    },
    "Good game (22 disp, 2 goals, 6 marks, 4 tackles)": {
        "kicks": 13, "handballs": 9, "marks": 6, "goals": 2,
        "tackles": 4, "clearances": 3, "inside_50s": 3,
        "effective_disposals": 15, "clangers": 2,
    },
    "Elite forward (15 disp, 5 goals, 8 marks_i50)": {
        "kicks": 10, "handballs": 5, "marks": 8, "goals": 5,
        "marks_inside_50": 5, "contested_marks": 3,
        "tackles": 2, "behinds": 2, "effective_disposals": 9,
        "clangers": 1,
    },
    "Elite midfielder (35 disp, 1 goal, 8 clears, 6 tackles)": {
        "kicks": 20, "handballs": 15, "marks": 6, "goals": 1,
        "tackles": 6, "clearances": 8, "inside_50s": 5,
        "effective_disposals": 25, "clangers": 3,
        "contested_possessions": 12,
    },
    "Perfect forward (20 disp, 8 goals, 10 marks_i50)": {
        "kicks": 14, "handballs": 6, "marks": 10, "goals": 8,
        "marks_inside_50": 8, "contested_marks": 5,
        "tackles": 3, "behinds": 3, "effective_disposals": 12,
        "clangers": 1,
    },
}

# Print header
header = f"{'Game Type':<50}"
for gw in goal_weights_to_test:
    header += f"  GW={gw}"
print(header)
print("-" * 70)

for game_name, game_stats in test_games.items():
    row_str = f"{game_name:<50}"
    for gw in goal_weights_to_test:
        raw = compute_raw(game_stats, gw)
        rating = normalise(raw)
        row_str += f"  {rating:5.2f}"
    print(row_str)

# Also show what the top 20 real games rate at each goal weight
print("\n\nTOP 10 REAL GAMES AT EACH GOAL WEIGHT")
print("=" * 70)
top20 = df_active.nlargest(20, "dream_team_points").copy()

for gw in goal_weights_to_test:
    top20[f"raw_gw{gw}"] = top20.apply(
        lambda r: compute_raw(r, gw), axis=1
    )
    top20[f"rating_gw{gw}"] = top20[f"raw_gw{gw}"].apply(normalise)

display_cols = ["player_name", "position_group", "goals", "dream_team_points"] + \
               [f"rating_gw{gw}" for gw in goal_weights_to_test]
print(top20[display_cols].head(10).to_string(index=False))

# Build a position-specific percentile rating from the competition distribution.
df_active["raw_score"] = df_active.apply(
    lambda r: compute_raw(r, DEFAULT_GOAL_WEIGHT), axis=1
)
df_active["position_percentile"] = df_active.groupby("position_group")["raw_score"].rank(
    method="max", pct=True
) * 100.0

# Add per-stat weight and contribution columns for every weighted stat.
weighted_stats = ["goals"] + list(WEIGHTS.keys())
for stat in weighted_stats:
    weight = DEFAULT_GOAL_WEIGHT if stat == "goals" else WEIGHTS[stat]
    df_active[f"weight_{stat}"] = weight
    df_active[f"contribution_{stat}"] = df_active.get(stat, 0).fillna(0) * weight

# Position rank and major position selection.
df_active["position_rank"] = df_active.groupby("position_group")["position_percentile"].rank(
    method="dense", ascending=False
)
df_active["percentile_rating"] = df_active["position_percentile"].apply(percentile_to_rating)

major_positions = ["Ruck", "Forward", "Midfielder", "Defender"]
positioned = df_active[df_active["position_group"].isin(major_positions)].copy()
positioned = positioned.sort_values(["position_group", "position_percentile", "raw_score"], ascending=[True, False, False])

# Take the top 10 players in each major position.
position_tops = []
for pos in major_positions:
    top_pos = positioned[positioned["position_group"] == pos].head(10).copy()
    top_pos["position_top_n"] = range(1, len(top_pos) + 1)
    position_tops.append(top_pos)

output_df = pd.concat(position_tops, ignore_index=True)

print("\nTOP 10 GAMES BY MAJOR POSITION WITH WEIGHTED STAT CONTRIBUTIONS")
print("=" * 70)
print(output_df[["player_name", "position_group", "position_top_n", "position_percentile", "percentile_rating", "raw_score"]].to_string(index=False))

# Build output columns including every weighted stat and contribution column.
base_cols = [
    "player_name", "team", "position_group", "round.roundNumber", "position_top_n",
    "position_percentile", "percentile_rating", "raw_score", "dream_team_points"
]
stat_cols = [stat for stat in weighted_stats if stat in output_df.columns]
weight_cols = [f"weight_{stat}" for stat in weighted_stats]
contribution_cols = [f"contribution_{stat}" for stat in weighted_stats]

output_cols = base_cols + stat_cols + weight_cols + contribution_cols
output_cols = [col for col in output_cols if col in output_df.columns]

csv_output_path = Path(__file__).resolve().parent / "top10_per_position_weighted_ratings.csv"
output_df[output_cols].to_csv(csv_output_path, index=False)
print(f"\nSaved top 10 per position weighted ratings to {csv_output_path}")