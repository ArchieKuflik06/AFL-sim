
class QuaterStats:
    def __init__(self, quarter_number):
        pass

    def get_stats(self, player, quarter_number):
        stats = player.current_game_stats
        for key, value in stats.to_dict().items():
            print(f"{key}: {value}")