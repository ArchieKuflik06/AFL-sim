
Description

A Python-based AFL feed simulator which currently takes fake event data to process and produce stats and a live game play feed.
Key features include the modelling of teams, players, match events, and possession chains.

Features

- Match simulation involving the creation and processing of AFL match data.
- tracks possessions and connected events throughout a chain of possession.
- Review long supports match review events and review outcomes enabling dynamic event handling
- Team and player models represents team rosters and individual player events.
- loads, creates, and processes events such as kicks, marks, and other AFL actions.
- Statistics — derives match, team, and player statistics from event and chain data.
- Event export — saves match event data to JSON.
- Player ratings — calculates positional ratings and weighted percentile-based scores using AFL statistics.

Weaknesses and improvements
- Figure out where to get legitimate data from to serve a real purposes
- Replace the data classes which are acting as place holders once the real purpose is found


To Run

python3 main.py

Project Structure
main.py — application entry point
builders — match and team construction
engines — event loading and match-processing logic
features — match, team, player, and chain models
game_stats — match and team statistics
rating_system — player ratings and AFL statistics
tests — automated test suite
events.json - stores fake game data
