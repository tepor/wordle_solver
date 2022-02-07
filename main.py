from audioop import avg
import json
import re
import random as r
import time

alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]

class Result:
    CORRECT = 2
    CLOSE = 1
    WRONG = 0


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
                if result is Result.WRONG:
                    self.wrongSet.add(c)
                elif result is Result.CORRECT:
                    self.correctList[pos] = c
                elif result is Result.CLOSE:
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
                result.append(str(Result.CORRECT))
            elif w in self.answer:
                result.append(str(Result.CLOSE))
            else:
                result.append(str(Result.WRONG))

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




def getValidWords(words, info):
    closeStrings = [
        f"(?=(?:.*{x.letter}.*){{{x.count},}})" for x in info.closeList
    ]

    wrongLists = [
        list(info.wrongSet),
        list(info.wrongSet),
        list(info.wrongSet),
        list(info.wrongSet),
        list(info.wrongSet)
    ]
    for x in info.closeList:
        for pos in x.notAt:
            wrongLists[pos].append(x.letter)
    wrongStrings = ["[^\\n" + "".join(x) + "]" for x in wrongLists]

    slotStrings = [
        w if c == "?" else c for w, c in zip(wrongStrings, info.correctList)
    ]

    pattern = "".join(closeStrings) + "".join(slotStrings) + "(?=\\\")"

    # print("Regex pattern:", pattern)
    compiled = re.compile(pattern)
    return compiled.findall(words)


def scoreWord(word, letterScore):
    score = 0
    for c in set(word):
        score += letterScore[c]
    return score


def rankWords(allWords, validWords, info):
    # Heuristic based on freqeuency of letters
    # Find the most common letters not in the known info
    ignoredLetters = list(info.wrongSet) + [x for x in info.correctList if x != "?"]
    letterScore = dict.fromkeys(alphabet, 0)
    for word in validWords:
        for c in word:
            if c in ignoredLetters:
                letterScore[c] = 0
            else:
                letterScore[c] += 2

    # Score each word and sort them
    # Should be done with a sort key but his is easier to inspect
    scores = [scoreWord(x, letterScore) for x in allWords]
    ranked = [x for _, x in sorted(zip(scores, allWords), reverse=True)]

    return ranked



print("Starting Worldle Solver")

# Load the word list
with open("wordle_solutions.json") as f:
    wordRaw = f.read()

wordList = json.loads(wordRaw)
print(f"Loaded legal word list of {len(wordList)} words")

with open("wordle_uncommon.json") as f:
    uncommonRaw = f.read()

uncommonList = json.loads(uncommonRaw)
print(f"Loaded uncommon word list of {len(uncommonList)} words")

mode = int(
    input("\nPlease choose one of the following:\n \
              1: Solver\n \
              2: Play game\n \
              3: Play game with solver \n \
              4: Auto-play\n"))

if mode == 1:
    print("\nStarting solver\n")

    info = KnownInfo()

    validWords = getValidWords(wordRaw, info)

    while (info.rowsLeft):

        print(f"\n{info.rowsLeft} guesses remaining")

        if len(validWords) > 3:
            ranked = rankWords(wordList + uncommonList, validWords, info)
            # print(ranked)
            print(f"Suggested guess: \"{ranked[0]}\"\n")
        elif len(validWords) > 1:
            ranked = rankWords(validWords, validWords, info)
            print(f"Suggested guess: \"{ranked[0]}\"\n")
        elif len(validWords) == 1:
            print(f"The answer is \"{validWords[0]}\"\n")
        else:
            ValueError("No more valid words")

        guessString = input("Please enter your guess\n")
        guessResult = input(
            "\nPlease enter the result of this guess\n(e.g. \"10020\" where 1 is yellow and 2 is green)\n"
        )
        resultList = [int(x) for x in guessResult]

        info.addGuess(Guess(guessString, resultList))

        print("Correct:", info.correctList)
        print("Close:",
              [f"{x.letter}:{x.count}:pos{x.notAt}" for x in info.closeList])
        print("Wrong:", info.wrongSet)

        validWords = getValidWords(wordRaw, info)
        print(f"{len(validWords)} valid words remaining:\n{validWords}")

elif mode == 2:
    print("\nStarting game\n")
    print(
        "Guess results are shown as a string of squares\n \
         matching the letters of the guess like \"⬜⬜🟨🟩⬜\"\n \
         ⬜: This letter is not in the answer\n \
         🟨: This letter is in the answer, but not this position\n \
         🟩: This letter is correct\n")

    game = Game(wordList, uncommonList)

    while game.rowsLeft and not game.solved:
        guess = input(
            f"\nPlease enter a guess ({game.rowsLeft} guesses remaining)\n")
        result = game.guess(guess)
        if result is not None:
            game.prettyPrintLastGuess()
            
    if game.solved:
        print(f"\nCongratulations! You guessed the correct answer: \"{game.answer}\"\n"\
              f"Solved in {6 - game.rowsLeft} guesses")
    else:
        print(f"\nGame over. The answer was \"{game.answer}\"")
    
    game.prettyPrintResults()

elif mode == 3:
    print("\nNot implemented\n")

elif mode == 4:
    print("\nStarting auto-play\n")
    startTime = time.time()

    rounds = len(wordList)
    results = []

    for round in range(rounds):
        game = Game(wordList, uncommonList, solutionNum=round)
        info = KnownInfo()
        validWords = getValidWords(wordRaw, info)

        print(f"\nStarting game {round + 1}/{rounds}")

        while game.rowsLeft and not game.solved:
            print(f"\n{game.rowsLeft} guesses remaining\n")

            # Factor out
            if len(validWords) > 3:
                ranked = rankWords(wordList + uncommonList, validWords, info)
                guessString = ranked[0]
                print(f"Best guess: \"{guessString}\"")
            elif len(validWords) > 1:
                ranked = rankWords(validWords, validWords, info)
                # Try this later with the worst word ([-1])
                guessString = ranked[0]
                print(f"Best guess: \"{guessString}\"")
            elif len(validWords) == 1:
                guessString = validWords[0]
                print(f"The answer is \"{guessString}\"")
            else:
                ValueError("No more valid words")

            result = game.guess(guessString)

            info.addGuess(Guess(guessString, [int(x) for x in result]))
            validWords = getValidWords(wordRaw, info)

            game.prettyPrintLastGuess()

            # time.sleep(2)

        if game.solved:
            print(f"\nSolver guessed the correct answer: \"{game.answer}\"\n"\
                f"Solved in {6 - game.rowsLeft} guesses")
            results.append(6 - game.rowsLeft)
        else:
            print(f"\nGame over. The answer was \"{game.answer}\"")
            results.append(7)

        game.prettyPrintResults()

        # time.sleep(2)

    endTime = time.time()

    print("\nAuto-play complete\n")
    print(f"Average guesses: {float(sum(results)) / float(len(results))}")
    print(f"Failures: {results.count(7)}")
    print(f"Time elapsed: {endTime-startTime}s")

    # Known failures: mimic, huger


else:
    print("\nInvalid choice\n")
