import json

from bin.event_creator import EventCreater


def test_write_events_json(tmp_path):
    creator = EventCreater()
    output_path = tmp_path / "events.json"

    event_data = [
        ("goal", "player-a", 5, 1, "team-a", {"is_effective": True}),
    ]
    scaled_event_data = [
        ("goal", "player-a", 1.0, 1, "team-a", {"is_effective": True}, 5),
    ]

    creator._write_events_json(event_data, scaled_event_data, output_path=output_path)

    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved[0]["event_type"] == "goal"
    assert saved[0]["player"] == "player-a"
    assert saved[0]["scaled_time"] == 1.0
    assert saved[0]["original_time"] == 5
