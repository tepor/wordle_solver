import json
import re
import time
from multiprocessing import Pool

import w_constants
import w_game
import w_info


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
    ignoredLetters = list(
        info.wrongSet) + [x for x in info.correctList if x != "?"]
    letterScore = dict.fromkeys(w_constants.ALPHABET, 0)
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

def solveGame(game_no):
    game = w_game.Game(wordList, uncommonList, solutionNum=game_no)
    info = w_info.KnownInfo()
    validWords = getValidWords(wordRaw, info)

    print(f"\nStarting game {game_no + 1}")

    while game.rowsLeft and not game.solved:
        # Factor out
        if len(validWords) > 3:
            ranked = rankWords(wordList + uncommonList, validWords, info)
            guessString = ranked[0]
        elif len(validWords) > 1:
            ranked = rankWords(validWords, validWords, info)
            # Try this later with the worst word ([-1])
            guessString = ranked[0]
        elif len(validWords) == 1:
            guessString = validWords[0]
        else:
            ValueError("No more valid words")

        result = game.guess(guessString)

        info.addGuess(w_info.Guess(guessString, [int(x) for x in result]))
        validWords = getValidWords(wordRaw, info)

    if game.solved:
        return 6 - game.rowsLeft
    else:
        return 7




# Very dangerous to do this in the global scope, but we're just
# learning python multiprocessing

# Load the word lists
with open("wordle_solutions.json") as f:
    wordRaw = f.read()

wordList = json.loads(wordRaw)
print(f"Loaded legal word list of {len(wordList)} words")

with open("wordle_uncommon.json") as f:
    uncommonRaw = f.read()

uncommonList = json.loads(uncommonRaw)
print(f"Loaded uncommon word list of {len(uncommonList)} words")


if __name__ == "__main__":
    print("Starting Worldle Solver")


    mode = int(
        input("\nPlease choose one of the following:\n \
                1: Solver\n \
                2: Play game\n \
                3: Play game with solver \n \
                4: Auto-play (visible)\n \
                5: Auto-play (as fast as possible)\n"))

    if mode == 1:
        print("\nStarting solver\n")

        info = w_info.KnownInfo()

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

            info.addGuess(w_info.Guess(guessString, resultList))

            print("Correct:", info.correctList)
            print("Close:",
                [f"{x.letter}:{x.count}:pos{x.notAt}" for x in info.closeList])
            print("Wrong:", info.wrongSet)

            validWords = getValidWords(wordRaw, info)
            print(f"{len(validWords)} valid words remaining:\n{validWords}")

    elif mode == 2:
        print("\nStarting game\n")
        print("Guess results are shown as a string of squares\n \
            matching the letters of the guess like \"⬜⬜🟨🟩⬜\"\n \
            ⬜: This letter is not in the answer\n \
            🟨: This letter is in the answer, but not this position\n \
            🟩: This letter is correct\n")

        w_game = w_game.Game(wordList, uncommonList)

        while w_game.rowsLeft and not w_game.solved:
            guess = input(
                f"\nPlease enter a guess ({w_game.rowsLeft} guesses remaining)\n")
            result = w_game.guess(guess)
            if result is not None:
                w_game.prettyPrintLastGuess()

        if w_game.solved:
            print(f"\nCongratulations! You guessed the correct answer: \"{w_game.answer}\"\n"\
                f"Solved in {6 - w_game.rowsLeft} guesses")
        else:
            print(f"\nGame over. The answer was \"{w_game.answer}\"")

        w_game.prettyPrintResults()

    elif mode == 3:
        print("\nNot implemented\n")

    elif mode == 4:
        print("\nStarting auto-play\n")
        startTime = time.time()

        rounds = len(wordList)
        results = []

        for round in range(rounds):
            game = w_game.Game(wordList, uncommonList, solutionNum=round)
            info = w_info.KnownInfo()
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

                info.addGuess(w_info.Guess(guessString, [int(x) for x in result]))
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

    elif mode == 5:
        print("\nStarting auto-play (as fast as possible)\n")
        startTime = time.time()

        with Pool() as pool:
            rounds = len(wordList)
            results = pool.map(solveGame, range(rounds))

        endTime = time.time()

        print("\nAuto-play complete\n")
        print(f"Average guesses: {float(sum(results)) / float(len(results))}")
        print(f"Failures: {results.count(7)}")
        print(f"Time elapsed: {endTime-startTime}s")

        # Known failures: mimic, huger

    else:
        print("\nInvalid choice\n")
