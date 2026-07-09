install.packages("fitzRoy", repos = "https://cloud.r-project.org")
library(fitzRoy)

# Fetch 2024 player stats game by game
stats <- fetch_player_stats(season = 2024)

# Save to CSV so Python can read it
write.csv(stats, "afl_stats_2024.csv", row.names = FALSE)

print(paste("Done — rows:", nrow(stats)))
print(colnames(stats))