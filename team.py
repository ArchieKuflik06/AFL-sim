class Team:
    def __init__(self, name, players, score):
        self.name = name
        self.players = players
        self.score = score

    def getScore(self):
        print(self.score)
        return self.score
    
    def getName(self):
        print(self.name)
        return self.name
    
    def getPlayers(self):
        print(self.players)
        return self.players