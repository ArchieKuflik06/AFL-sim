from game_stats.Data_Classes import TeamStats

class CalcTeamStats:
    CHAIN_SCORE_STAT_BY_START_REASON = {
        "turnover": "points_from_turnovers",
        "kick_in": "points_from_kick_ins",
        "stoppage": "points_from_stoppage",
        "center_bounce": "points_from_center_bounces",
    }

    def _apply_chain_player_stats(self, chain):
        for player in chain.get_score_involvement_players():
            stats = getattr(player, "current_game_stats", None)
            if stats is not None:
                stats.inc("score_involvements")

        if self.team_stats is not None:
            self.team_stats.inc("score_involvements")

        for player in chain.get_goal_assist_players():
            stats = getattr(player, "current_game_stats", None)
            if stats is not None:
                stats.inc("goal_assists")

        if self.team_stats is not None:
            self.team_stats.inc("goal_assists")

    def _infer_score_stat_name(self, chain):
        if chain is None:
            return None

        start_reason = getattr(chain, "start_reason", None)
        if start_reason in self.CHAIN_SCORE_STAT_BY_START_REASON:
            return self.CHAIN_SCORE_STAT_BY_START_REASON[start_reason]

        end_reason = getattr(chain, "end_reason", None)
        if end_reason in {"goal", "behind", "rushed_behind"}:
            return "points_from_center_bounces"

        if end_reason in {"out_of_bounds", "tackle"}:
            return "points_from_stoppage"

        for event in reversed(getattr(chain, "events", [])):
            event_type = getattr(event, "event_type", None)
            if event_type == "out_of_bounds":
                return "points_from_stoppage"
            if event_type == "tackle":
                return "points_from_stoppage"
            if event_type == "free_kick":
                reason = getattr(event, "reason", None)
                if getattr(reason, "value", None) == "Lasso":
                    return "points_from_stoppage"
                break

        return None

    def __init__(self, team, team_stats: TeamStats):
        self.team = team
        self.team_stats = team_stats

    def calculate_time_winning(self, winning: bool, time_delta: int):
        if winning:
            self.team_stats.inc("time_winning", amount=time_delta)

    def on_chain_closed(self, chain):
        if chain.team != self.team or not chain.resulted_in_score():
            return

        self._apply_chain_player_stats(chain)

        stat_name = self._infer_score_stat_name(chain)
        if stat_name is None:
            return

        self.team_stats.inc(stat_name, amount=chain.points_scored())


