import pandas as pd
import numpy as np
from pathlib import Path

csv_path = Path(__file__).resolve().parent / "afl_stats_2024.csv"
df = pd.read_csv(csv_path)

df = df.rename(columns={
    "player.player.player.givenName":   "first_name",
    "player.player.player.surname":     "last_name",
    "player.player.player.playerId":    "player_id",
    "player.player.position":           "position",
    "team.name":                        "team",
    "clearances.totalClearances":       "clearances",
    "extendedStats.effectiveKicks":     "effective_kicks",
    "extendedStats.effectiveDisposals": "effective_disposals",
    "extendedStats.hitoutsToAdvantage": "hitouts_to_advantage",
    "extendedStats.groundBallGets":     "ground_ball_gets",
    "extendedStats.interceptMarks":     "intercept_marks",
    "extendedStats.spoils":             "spoils",
    "extendedStats.pressureActs":       "pressure_acts",
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
    "C":    "Midfielder",   # Centre
    "WL":   "Midfielder",   # Wing Left
    "WR":   "Midfielder",   # Wing Right
    "RR":   "Midfielder",   # Rover
    "R":    "Midfielder",   # Ruck Rover
    "CHF":  "Forward",      # Centre Half Forward
    "FF":   "Forward",      # Full Forward
    "FPL":  "Forward",      # Forward Pocket Left
    "FPR":  "Forward",      # Forward Pocket Right
    "HFFL": "Forward",      # Half Forward Flank Left
    "HFFR": "Forward",      # Half Forward Flank Right
    "CHB":  "Defender",     # Centre Half Back
    "FB":   "Defender",     # Full Back
    "BPL":  "Defender",     # Back Pocket Left
    "BPR":  "Defender",     # Back Pocket Right
    "HBFL": "Defender",     # Half Back Flank Left
    "HBFR": "Defender",     # Half Back Flank Right
    "RK":   "Ruck",         # Ruck
    "INT":  "Interchange",
    "SUB":  "Interchange",
    "EMERG":"Interchange",
}

df["position_group"] = df["position"].map(position_map).fillna("Unknown")
df_active = df[~df["position_group"].isin(["Interchange", "Unknown"])].copy()

print(f"Active player-game rows: {len(df_active)}")
print(f"Position breakdown:\n{df_active['position_group'].value_counts()}\n")

STAT_COLS = [
    "kicks", "handballs", "disposals", "marks", "goals", "behinds",
    "tackles", "hitouts", "clearances", "inside_50s", "rebound_50s",
    "contested_possessions", "marks_inside_50", "contested_marks",
    "frees_for", "frees_against", "clangers", "goal_assists",
    "effective_disposals", "hitouts_to_advantage", "intercept_marks",
    "spoils", "ground_ball_gets", "one_percenters", "knock_ons",
]

percentiles = [25, 50, 75, 90, 95, 99]

print("=" * 70)
print("STAT DISTRIBUTIONS — 2024 AFL (per player per game, active players)")
print("=" * 70)

for col in STAT_COLS:
    if col not in df_active.columns:
        print(f"\n{col.upper()} — NOT IN DATA")
        continue
    vals = df_active[col].dropna()
    pcts = np.percentile(vals, percentiles)
    print(f"\n{col.upper()}")
    print(f"  Mean: {vals.mean():.2f}  Std: {vals.std():.2f}  Max: {vals.max():.0f}")
    for p, v in zip(percentiles, pcts):
        print(f"  {p:3d}th pct: {v:.1f}")

print("\n" + "=" * 70)
print("AVERAGE STATS BY POSITION")
print("=" * 70)
cols_for_pos = [c for c in STAT_COLS if c in df_active.columns]
print(df_active.groupby("position_group")[cols_for_pos].mean().round(2).to_string())

print("\n" + "=" * 70)
print("TOP 20 INDIVIDUAL GAMES — Dream Team Points as benchmark")
print("=" * 70)
top_cols = [c for c in ["player_name", "team", "position_group",
                          "round.roundNumber", "kicks", "handballs",
                          "marks", "goals", "tackles", "clearances",
                          "dream_team_points"] if c in df_active.columns]
top = df_active.nlargest(20, "dream_team_points")[top_cols]
print(top.to_string(index=False))

print("\n" + "=" * 70)
print("SUGGESTED RATING WEIGHTS — derived from 75th percentile")
print("=" * 70)

weights = {}
for col in STAT_COLS:
    if col not in df_active.columns:
        continue
    if col == "goals":
        weights[col] = 3.5
        continue
    p75 = np.percentile(df_active[col].dropna(), 75)
    if p75 > 0:
        w = round(1.0 / p75, 3)
    else:
        p95 = np.percentile(df_active[col].dropna(), 95)
        w = round(1.0 / p95, 3) if p95 > 0 else 0.0
    weights[col] = w

for col in ("frees_against", "clangers"):
    if col in weights:
        weights[col] = -abs(weights[col])

for stat, w in sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True):
    sign = "+" if w >= 0 else ""
    print(f"  {stat:<35} {sign}{w:.3f}")