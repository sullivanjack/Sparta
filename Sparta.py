import csv

PLAYER_AMOUNT = 16

class data:
    wins = 14
    losses = 0
    ranking = 0
    scoreboard = [ [ "Ignore" for i in range(20) ] for j in range(20) ]
    currentHole = 0
    
    def reset():
        data.wins = 14
        data.losses = 0
        data.ranking = 0
        data.currentHole += 1

class Player:
    def __init__(self, name, handicap, scores):
        self.name = name
        self.handicap = handicap
        self.scores = scores
        self.wins = 0
        self.losses = 0
        
    def __str__(self):
        #return "{0:20}   \n".format(self.getName(),  ''.join(str(x) for x in self.getScores()))
        #return str(self.getName() + "\t" + ''.join(str(x) for x in self.getScores()))
        return "<Player " + self.getName() + " Object>"
    
    def __repr__(self):
        #return "{0:20}   \n".format(self.getName(),  ''.join(str(x) for x in self.getScores()))
        #return str(self.getName() + "\t" + ' '.join(str(x) for x in self.getScores()) + " \n")
        return "<Player " + self.getName() + " Object>"
    
    def getScore(self, holeNumber):
        if(holeNumber > 18 or holeNumber < 1):
            print("Hole number out of range dummy")
            return -1
        return self.scores[holeNumber - 1]

    def getScores(self):
        return self.scores

    def getHandicap(self):
        return self.handicap

    def getName(self):
        return self.name

    def setHoleScore(self, hole, score):
        self.scores[hole - 1] = score
        
    def getHoleScore(self, hole):
        return self.scores[hole]

    def addWins(self, wins):
        self.wins = self.wins + wins
    
    def addLosses(self, losses):
        self.losses = self.losses + losses
        
    def getWins(self):
        return self.wins
    
    def getLosses(self):
        return self.losses
    
    
    
    
# New
def getGroups(scores):
    # Scores will be a list with [player name, player score, player object]
    lastScore = 0
    index = -1
    groups = [[],[],[],[],[],[],[],[],[],[],[],[],[]] 
    for s in scores:
        if(s[1] == lastScore):
            groups[index].append(s)
        elif(s[1] > lastScore):
            index+=1
            lastScore = s[1]
            groups[index].append(s)
        else:
            lastScore+=1
    return groups
       
def getScores(players, hole):
    scores = []
    
    index = 0
    for p in players:
        s = p.getScore(hole)
        scores.append( (p.getName(), s, p) )
        index += 1
    scores.sort(key = lambda x: x[1])
    return scores

def printGroup(group):
    print("###################")
    for g in group:
        for gg in g:
            print(gg)
        print("")
    print("###################")



#wins = 12
def recursiveGroups(scores, hole):
    groups = getGroups(scores)

    for g in groups:
        if(len(g) == 1):
            print(g[0][0], " - W/L", data.wins, "/", data.losses)
            data.scoreboard[data.currentHole][data.ranking] = g[0][0]
            data.ranking += 1
            g[0][2].addWins(data.wins)
            g[0][2].addLosses(data.losses)
            data.wins -= 1
            data.losses += 1
        elif(len(g) > 1):
            players = []
            for p in g:
                players.append(p[2])
            if(hole + 1 > 18):
                data.wins -= (len(g) - 1)            
                for p in g:
                    print(p[0], " - W/L", data.wins, "/", data.losses, " (tie)")
                    data.scoreboard[data.currentHole][data.ranking] = p[0]
                    data.ranking += 1
                    p[2].addWins(data.wins)
                    p[2].addLosses(data.losses)
                data.wins -= 1
                data.losses += len(g)
                continue
            nextHoleScores = getScores(players, hole + 1)
            recursiveGroups(nextHoleScores, hole + 1)

# ------------------------------------------------------------------------
#       main
# ------------------------------------------------------------------------
        

filename = "Sparta2019_Day1.csv"
outputFile = "Sparta2019_Day1_Output.csv"
handicaps = [] # (handicap raiting, hole number)
players = [] #   (golfer name, handicap, hole scores)

with open(filename, mode = 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    line_count = 0
    for row in csv_reader:
        if(row["Name"] == "Handicap"):
            hole = 1
            for key, value in row.items():
                if(not (key == "Name" or key == "Handicap")):
                    handicaps.append( (int(value), hole) )
                    hole += 1
        else:
            name = row["Name"]
            handi = int(row["Handicap"])
            scores = []
            for key, value in row.items():
                if(not (key == "Name" or key == "Handicap")):
                    scores.append(int(value))
            p = Player(name, handi, scores)
            players.append(p)
            
handicaps.sort(key = lambda x: x[0])

# At this point we will have our data read into the handicaps and players lists
# We will now need to calcualte adujusted scores based on handicaps provided. 
print(players)
print(handicaps)

for p in players:
    print(p.getName(), " ", p.getScores())

for p in players:
    name = p.getName()
    handi = p.getHandicap()
    while(handi > 0):      
        for hole in handicaps:
            if(handi == 0):
                break
            handicapHole = hole[0]
            holeNumber = hole[1]
            holeScore = p.getScore(holeNumber)
            p.setHoleScore(holeNumber, holeScore-1)
            handi -= 1      

# Write the handicaps to a CSV file. 
f = open(outputFile, "a")
f.write("SCORES ADJUSTED FOR HANDICAPS\n")
for p in players:
    line = []
    line.append(p.getName() + ",")
    for h in p.getScores():
        line.append(str(h) + ",")
    s = ''.join(line)
    f.write(s + "\n")


# Above calculates the new scores with the handicap subtractred from each hole.
print("\n\n")
for p in players:
    print(p.getName(), " ", p.getScores())

for hole in range(1, 19):
    print("HOLE: ", hole)
    scores = []

    index = 0
    for p in players:
        s = p.getScore(hole)
        scores.append( (p.getName(), s, p) )
        index += 1
    scores.sort(key = lambda x: x[1])
    data.reset()
    recursiveGroups(scores, hole)
    print()
    
print(data.scoreboard)
    
f.write("\n")

for i in range(0, 20):
    line = []
    for j in range(0, 20):
        line.append(data.scoreboard[j][i] + ",")
    s = ''.join(line)
    f.write(s + "\n")
    #print(data.scoreboard[j][i])
    print()

f.write("\n")

for p in players:
    f.write(p.getName() + "," + str(p.getWins()) + "," + str(p.getLosses()) + "," + str((p.getWins() - p.getLosses()) * .1))
    f.write("\n")
    print(p.getName(), " ", p.getWins(), " | ", p.getLosses(), " | ", p.getWins() - p.getLosses())



    



















