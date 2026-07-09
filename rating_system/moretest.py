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

# ── Cleaned weights — no double counting ──────────────────────────────────
# marks_inside_50, contested_marks, intercept_marks are BONUSES only
# (extra on top of base mark weight, not replacements)
# effective_disposals removed — already captured by kicks/handballs
# disposals removed — double counts kicks + handballs
WEIGHTS = {
    # Volume stats
    "kicks":                 0.08,
    "handballs":             0.05,
    "marks":                 0.15,
    "tackles":               0.25,
    "clearances":            0.35,
    "inside_50s":            0.20,
    "rebound_50s":           0.25,
    "ground_ball_gets":      0.15,
    "one_percenters":        0.15,
    "spoils":                0.20,
    "hitouts":               0.03,   # low — only rucks get these

    # Scoring
    "goals":                 1.75,   # test value — adjust after seeing distribution
    "behinds":               0.20,
    "goal_assists":          0.60,

    # Quality bonuses — on top of base mark weight
    "marks_inside_50":       0.40,   # bonus for marking inside 50
    "contested_marks":       0.40,   # bonus for contested mark
    "intercept_marks":       0.40,   # bonus for intercept mark
    "hitouts_to_advantage":  0.25,

    # Contested possession quality
    "contested_possessions": 0.08,
    "frees_for":             0.40,

    # Penalties
    "frees_against":        -0.40,
    "clangers":             -0.20,
}

def compute_raw(row):
    return sum(row.get(col, 0) * w for col, w in WEIGHTS.items())

df_active["raw"] = df_active.apply(compute_raw, axis=1)

# ── Fixed ceiling — set manually based on what should be "near 10" ────────
# Look at the distribution first, then decide
print("RAW SCORE DISTRIBUTION WITH CLEANED WEIGHTS")
print("=" * 50)
for p in [10, 25, 50, 75, 90, 95, 99, 99.5, 99.9]:
    print(f"  {p:5.1f}th pct: {np.percentile(df_active['raw'], p):.2f}")
print(f"  Max:         {df_active['raw'].max():.2f}")
print(f"  Min:         {df_active['raw'].min():.2f}")

# Set ceiling at 99.5th percentile — only 0.5% of games reach 10.0
RAW_CEILING = np.percentile(df_active["raw"], 99.5)
RAW_FLOOR   = np.percentile(df_active["raw"], 5)
EXPONENT    = 0.6

print(f"\nUsing ceiling: {RAW_CEILING:.2f}, floor: {RAW_FLOOR:.2f}")

def normalise(raw):
    clamped = max(RAW_FLOOR, raw)
    shifted = clamped - RAW_FLOOR
    ceiling_shifted = RAW_CEILING - RAW_FLOOR
    linear = min(shifted / ceiling_shifted, 1.0)
    return round((linear ** EXPONENT) * 10, 2)

df_active["rating"] = df_active["raw"].apply(normalise)

# ── Rating distribution ───────────────────────────────────────────────────
print("\nRATING DISTRIBUTION (0-10)")
print("=" * 50)
for p in [10, 25, 50, 75, 90, 95, 99, 99.5, 99.9]:
    print(f"  {p:5.1f}th pct: {np.percentile(df_active['rating'], p):.2f}")
print(f"  Max:         {df_active['rating'].max():.2f}")

# ── Top games overall ─────────────────────────────────────────────────────
print("\nTOP 15 GAMES OVERALL")
print("=" * 70)
cols = ["player_name", "position_group", "goals", "kicks",
        "marks", "clearances", "tackles", "raw", "rating"]
print(df_active.nlargest(15, "raw")[cols].to_string(index=False))

# ── Top games by position ─────────────────────────────────────────────────
for pos in ["Midfielder", "Forward", "Defender", "Ruck"]:
    print(f"\nTOP 10 {pos.upper()} GAMES")
    print("=" * 70)
    subset = df_active[df_active["position_group"] == pos]
    print(subset.nlargest(50, "raw")[cols].to_string(index=False))

# ── Average game ratings by position ─────────────────────────────────────
print("\nAVERAGE RATING BY POSITION")
print("=" * 50)
print(df_active.groupby("position_group")["rating"].describe().round(2).to_string())