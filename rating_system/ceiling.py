import pandas as pd
import numpy as np
from pathlib import Path

csv_path = Path(__file__).resolve().parent / "afl_stats_2024.csv"
df = pd.read_csv(csv_path)


df = df.rename(columns={
    "player.player.player.givenName":   "first_name",
    "player.player.player.surname":     "last_name",
    "player.player.position":           "position",
    "clearances.totalClearances":       "clearances",
    "extendedStats.effectiveDisposals": "effective_disposals",
    "extendedStats.hitoutsToAdvantage": "hitouts_to_advantage",
    "extendedStats.interceptMarks":     "intercept_marks",
    "extendedStats.spoils":             "spoils",
    "extendedStats.groundBallGets":     "ground_ball_gets",
    "marksInside50":                    "marks_inside_50",
    "contestedMarks":                   "contested_marks",
    "contestedPossessions":             "contested_possessions",
    "freesFor":                         "frees_for",
    "freesAgainst":                     "frees_against",
    "rebound50s":                       "rebound_50s",
    "inside50s":                        "inside_50s",
    "goalAssists":                      "goal_assists",
    "onePercenters":                    "one_percenters",
    "dreamTeamPoints":                  "dream_team_points",
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

WEIGHTS = {
    "kicks":                 0.01, #manual
    "handballs":             0.05, #manua
    "marks":                 0.167,
    "goals":                 3.500,
    "behinds":               0.300,
    "tackles":               0.250,
    "clearances":            0.333,
    "inside_50s":            0.333,
    "rebound_50s":           0.333,
    "contested_possessions": 0.125,
    "marks_inside_50":       1.000,
    "contested_marks":       1.000,
    "frees_for":             1.000,
    "frees_against":        -1.000,
    "clangers":             -0.250,
    "goal_assists":          1.000,
    "effective_disposals":   0.067,
    "spoils":                0.500,
    "ground_ball_gets":      0.200,
    "one_percenters":        0.333,
    "intercept_marks":       1.000,
}

def compute_raw(row):
    return sum(row.get(col, 0) * w for col, w in WEIGHTS.items())

df_active["raw_score"] = df_active.apply(compute_raw, axis=1)

# ── What ceiling and floor to use ─────────────────────────────────────────
print("RAW SCORE DISTRIBUTION — sets your ceiling/floor values")
print("=" * 50)
for p in [10, 25, 50, 75, 90, 95, 99, 99.5, 99.9]:
    print(f"  {p:5.1f}th pct: {np.percentile(df_active['raw_score'], p):.2f}")
print(f"  Max:         {df_active['raw_score'].max():.2f}")
print(f"  Min:         {df_active['raw_score'].min():.2f}")

# ── What different curve exponents produce ────────────────────────────────
print("\nHOW CURVE EXPONENT AFFECTS RATINGS")
print("=" * 50)
print("(using 99th pct as ceiling, 10th pct as floor)")

raw_ceiling = np.percentile(df_active["raw_score"], 99)
raw_floor   = np.percentile(df_active["raw_score"], 10)

def normalise(raw, ceiling, floor, exponent):
    clamped = max(floor, raw)
    shifted = clamped - floor
    ceiling_shifted = ceiling - floor
    linear = min(shifted / ceiling_shifted, 1.0)
    curved = linear ** exponent
    return round(curved * 10, 2)

exponents = [0.5, 0.6, 0.7, 0.8]
percentile_labels = [10, 25, 50, 75, 90, 95, 99, 99.9]

header = f"{'Percentile':<12}"
for e in exponents:
    header += f"  exp={e}"
print(header)
print("-" * 50)

for p in percentile_labels:
    raw = np.percentile(df_active["raw_score"], p)
    row = f"{p:<12}"
    for e in exponents:
        rating = normalise(raw, raw_ceiling, raw_floor, e)
        row += f"  {rating:6.2f}"
    print(row)

# Max possible
row = f"{'Max':<12}"
for e in exponents:
    rating = normalise(df_active["raw_score"].max(), raw_ceiling, raw_floor, e)
    row += f"  {rating:6.2f}"
print(row)

# ── Top 10 games at each exponent ─────────────────────────────────────────
print("\nTOP 10 REAL GAMES — ratings at each exponent")
print("=" * 50)
top10 = df_active.nlargest(10, "raw_score").copy()

for e in exponents:
    top10[f"rating_{e}"] = top10["raw_score"].apply(
        lambda r: normalise(r, raw_ceiling, raw_floor, e)
    )

display_cols = ["player_name", "position_group", "goals", "kicks",
                "marks", "clearances", "raw_score"] + \
               [f"rating_{e}" for e in exponents]
print(top10[display_cols].to_string(index=False))