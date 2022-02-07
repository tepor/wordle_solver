import w_constants


class Guess:

    def __init__(self, guessString, result):
        self.string = guessString
        self.result = result  # [0,1,0,2,0]


class Close:

    def __init__(self, letter, position, count):
        self.letter = letter
        self.notAt = {position}
        self.count = count

    def update(self, position, count):
        self.notAt.add(position)
        self.count = max(self.count, count)


class KnownInfo:

    def __init__(self):
        self.guesses = []
        self.correctList = ["?", "?", "?", "?", "?"]
        self.closeList = []
        self.wrongSet = set()
        self.rowsLeft = 6

    def rebuild(self):
        for g in self.guesses:
            for pos, (c, result) in enumerate(zip(g.string, g.result)):
                if result is w_constants.Result.WRONG:
                    self.wrongSet.add(c)
                elif result is w_constants.Result.CORRECT:
                    self.correctList[pos] = c
                elif result is w_constants.Result.CLOSE:
                    count = g.string.count(c)
                    close = next((x for x in self.closeList if x.letter == c),
                                 None)
                    if close is not None:
                        close.update(pos, count)
                    else:
                        self.closeList.append(Close(c, pos, count))
                else:
                    raise Exception("Wrong letter type")

    def addGuess(self, guess):
        self.guesses.append(guess)
        self.rebuild()
        self.rowsLeft -= 1