import json
from engines.MatchEngine import MatchEngine
import features.PlayerEvents

print(features.PlayerEvents.__file__)

def main():
    with open("events.json") as f:
        raw_events = json.load(f)

    engine = MatchEngine()
    engine.create_match()
    match = engine.run(raw_events)

if __name__ == "__main__":
    main()