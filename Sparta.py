import csv

PLAYER_AMOUNT = 20

class data:
    wins = PLAYER_AMOUNT - 1
    losses = 0
    ranking = 0
    scoreboard = [ [ "Ignore" for i in range(28) ] for j in range(28) ]
    currentHole = 0
    
    def reset():
        data.wins = PLAYER_AMOUNT - 1
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
        self.money = 0
        
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
    
    def getFront9Score(self):
        total = 0
        for i in range(1, 10):
            total = total + self.getScore(i)
        return total
    
    def getBack9Score(self):
        total = 0
        for i in range(10, 19):
            total = total + self.getScore(i)
        return total
    
    def getTotalScore(self):
        return self.getFront9Score() + self.getBack9Score()
        
    def addMoney(self, m):
        self.money = self.money + m
    
    def getMoney(self):
        return self.money
    
    
# player - player object
# hole is a number  1 - hole inclusive
def getTotalScoreThroughHole(player, hole):
    total = 0
    for i in range(1, hole + 1):
        total = total + player.getScore(i)
    return total
    
# New
def getGroups(scores):
    # Scores will be a list with [player name, player score, player object]
    lastScore = 0
    index = -1
    groups = [[],[],[],[],[],[],[],[],[],[],[],[],[], [], [], [], []] 
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
 
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Arguments to the Sparta Prog")
    parser.add_argument("--inputFile", help="Name of input file.", required=True)
    args = parser.parse_args()
    
    filename = args.inputFile
    outputFile = "{}_Output.csv".format(args.inputFile.split(".")[0])
    
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

    #exclusive of 19
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

    for i in range(0, PLAYER_AMOUNT+4):
        line = []
        for j in range(0, 20):
            line.append(data.scoreboard[j][i] + ",")
        s = ''.join(line)
        f.write(s + "\n")
        #print(data.scoreboard[j][i])
        print()

    f.write("\n")

    f.write("Player, Wins, Losses, Wins-Losses * -1 ")
    f.write("\n")
    for p in players:
        totalMoney = ((p.getWins() - p.getLosses()) * .1)
        p.addMoney(totalMoney)
        f.write(p.getName() + "," + str(p.getWins()) + "," + str(p.getLosses()) + "," + str(totalMoney))
        f.write("\n")
        print(p.getName(), " ", p.getWins(), " | ", p.getLosses(), " | ", p.getWins() - p.getLosses())


    print("--------- FRONT 9 -----------------")
    front9Scores = []
    for p in players:
        total = p.getFront9Score()
        print("{} scored a net {} through the front 9".format(p.getName(), total))
        front9Scores.append((p, total))

    print(front9Scores) 
    front9Scores.sort(key=lambda x: x[0].getFront9Score())


    f.write("\n")
    f.write("Player, Front 9 Wins, Front 9 Losses, Wins-Losses *.5 \n")
    scores = []
    for x in front9Scores:
        scores.append([x[0].getName(), x[1], x[0]])
    groups = getGroups(scores)

    numOfGroups = 0
    for g in groups:
        if g:
            numOfGroups = numOfGroups + 1
    print(numOfGroups)

    playerCount = PLAYER_AMOUNT
    lossesCount = 0
    for x in range(0, numOfGroups):
        g = groups[x]
        totalWins = (len(g) - playerCount) * -1
        totalLosses = lossesCount
        lossesCount = lossesCount + len(g)
        totalMoney = .5 * (totalWins - totalLosses)
        playerCount = playerCount - len(g)
        for y in g:
            y[2].addMoney(totalMoney)
            f.write("{}, {}, {}, {} \n".format(y[2].getName(), totalWins, totalLosses, totalMoney))
            print("{} player beat {} players on the front 9, and lost to {} players, for ${} dollars".format(y[2].getName(), totalWins, totalLosses, totalMoney))


    print("---------  BACK 9 -----------------")
    back9Scores = []
    for p in players:
        total = p.getBack9Score()
        print("{} scored a net {} through the back 9".format(p.getName(), total))
        back9Scores.append((p, total))

    print(back9Scores) 
    back9Scores.sort(key=lambda x: x[0].getBack9Score())


    f.write("\n")
    f.write("Player, Back 9 Wins, Back 9 Losses, Wins-Losses *.5 \n")
    scores = []
    for x in back9Scores:
        scores.append([x[0].getName(), x[1], x[0]])
    groups = getGroups(scores)

    numOfGroups = 0
    for g in groups:
        if g:
            numOfGroups = numOfGroups + 1
    print(numOfGroups)

    playerCount = PLAYER_AMOUNT
    lossesCount = 0
    for x in range(0, numOfGroups):
        g = groups[x]
        totalWins = (len(g) - playerCount) * -1
        totalLosses = lossesCount
        lossesCount = lossesCount + len(g)
        totalMoney = .5 * (totalWins - totalLosses)
        playerCount = playerCount - len(g)
        for y in g:
            y[2].addMoney(totalMoney)
            f.write("{}, {}, {}, {} \n".format(y[2].getName(), totalWins, totalLosses, totalMoney))
            print("{} player beat {} players on the back 9, and lost to {} players, for ${} dollars".format(y[2].getName(), totalWins, totalLosses, totalMoney))        

    print("---------  Full 18 -----------------")
    full18Scores = []
    for p in players:
        total = p.getTotalScore()
        print("{} scored a net {} through the full 18".format(p.getName(), total))
        full18Scores.append((p, total))

    print(full18Scores) 
    full18Scores.sort(key=lambda x: x[0].getTotalScore())


    f.write("\n")
    f.write("Player, Full 18 Wins, Full 18 Losses, Wins-Losses *.5 \n")
    scores = []
    for x in full18Scores:
        scores.append([x[0].getName(), x[1], x[0]])
    groups = getGroups(scores)

    numOfGroups = 0
    for g in groups:
        if g:
            numOfGroups = numOfGroups + 1
    print(numOfGroups)

    playerCount = PLAYER_AMOUNT
    lossesCount = 0
    for x in range(0, numOfGroups):
        g = groups[x]
        totalWins = (len(g) - playerCount) * -1
        totalLosses = lossesCount
        lossesCount = lossesCount + len(g)
        totalMoney = .5 * (totalWins - totalLosses)
        playerCount = playerCount - len(g)
        for y in g:
            y[2].addMoney(totalMoney)
            f.write("{}, {}, {}, {} \n".format(y[2].getName(), totalWins, totalLosses, totalMoney))
            print("{} player beat {} players on the full 18, and lost to {} players, for ${} dollars".format(y[2].getName(), totalWins, totalLosses, totalMoney))

    f.write("\n Player Name, Total Money \n")
    for p in players:
        print("{} {} ".format(p.getName(),p.getMoney()))
        f.write("{}, {} \n".format(p.getName(), p.getMoney()))













