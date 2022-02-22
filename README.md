# wordle-solver

Optimally\* solves Wordle using entropy.

\*Program only looks one layer deep, optimization has room to improve. 

# Execution

Run in command line by navigating to the directory with wordle.py and typing `python wordle.py` (or `python3 wordle.py` if Python 2.X is still your default).
- With no command line arguments the program will solve today's Wordle and output in the same format you get when using the "Share" function on the Wordle website.
- Set the **first** command line argument to 'true' to see the guesses the program uses (and the answer to the Wordle). Ex. `python wordle.py true` will guess today's wordle and output each of it's guesses along with the emoji matrix of which letters were correct for that guess.
 - Set the **second** command line argument to any integer from 0 to 2308 to solve that day's Wordle (E.g. Wordle 247 is the Wordle for 02-21-2022. This number increments daily.) Ex: `python wordle.py false 247` will guess the Wordle for day 247 without printing the guesses. 


# Accuracy Benchmarking

Averages 2.88 attempts to guess the word if each each daily word is removed as a possible answer after being correctly guessed. Fails to guess the word 0 times using this strategy.

Averages 3.59 attempts if each correct answer is not then removed from the answer space. Fails to guess the word (takes more than 6 guesses) 10 times (0.43%) using this strategy. 
