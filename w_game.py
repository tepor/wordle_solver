import random as r

import w_constants


class Game:

    def __init__(self, solutions, uncommon, solutionNum=None):
        self.solutions = solutions
        self.uncommon = uncommon
        self.rowsLeft = 6
        self.rows = []
        self.solved = False
        if solutionNum:
            self.answer = self.solutions[solutionNum]
        else:
            self.answer = r.choice(self.solutions)

    def guess(self, word):
        if word not in self.solutions + self.uncommon:
            print("Invalid word")
            return None

        result = []
        for w, a in zip(list(word), list(self.answer)):
            if w == a:
                result.append(str(w_constants.Result.CORRECT))
            elif w in self.answer:
                result.append(str(w_constants.Result.CLOSE))
            else:
                result.append(str(w_constants.Result.WRONG))

        resultString = "".join(result)
        if resultString == "22222":
            self.solved = True

        self.rowsLeft -= 1
        self.rows.append((word, resultString))

        return resultString

    def colouriseResult(result):

        def colourise(c):
            if c == "2":
                return "🟩"
            elif c == "1":
                return "🟨"
            else:
                return "⬜"

        return "".join([colourise(x) for x in result])

    def prettyPrintLastGuess(self):
        colourResult = Game.colouriseResult(self.rows[-1][1])
        print("\n " + " ".join(self.rows[-1][0].upper()))
        print(colourResult)

    def prettyPrintResults(self):
        for row in self.rows:
            print(Game.colouriseResult(row[1]))
