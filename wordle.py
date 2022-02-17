import numpy as np
import plotly.graph_objects as go
import re
import copy

# Function to store an updated answers list (mostly used to increment the number for the word of the day).
# @param num - number of the day to add to the answers list.
# @param answers - list of possible answers.
def store_answers(num, answers):
    answers.append(str(num))
    with open('answers.csv', 'w') as f:
        for i in answers:
            f.write(str(i) + '\n')


# Function to open all required files into memory.
# @returns num - index of current word of the day.
# @returns primary_answers - list of all answers.
# @returns initial_entropy - dictionary of initial entropy values.
def open_files():
    with open('answers.csv') as f:
        primary_answers = f.read().splitlines()
    num = int(primary_answers[-1])
    del primary_answers[-1]
    with open('initial_entropy.csv') as f:
        temp = f.read().splitlines()
    initial_entropy = {}
    for i in temp:
        initial_entropy[i.split(',')[0]] = i.split(',')[1]
    return num, primary_answers, initial_entropy


# Function to check the letters and their position of the input against the target word.
# @param word - input word to check against the target word.
# @param target - word to check against
# @returns - array containing the matching information.
# 0=letter not in target (grey)  1=letter in target but in wrong position (yellow) 2=letter in target and in correct position (green).
def check_word(word, target):
    # Array to store match info in
    match = [-1, -1, -1, -1, -1]
    # Check for any exact matches first so we don't double dip with duplicate letters.
    for letter_index in range(5):
        # Check if letter in word is the same as and in the same position as in target.
        if word[letter_index] == target[letter_index]:
            match[letter_index] = 2
            # If we find the letter in target, replace it with a character so we cannot find it again. Allows use of repeated letters.
            target = target[:letter_index] + '+' + target[letter_index + 1:]
    for letter_index in range(5):
        for target_letter_index in range(5):
                # Check letter against all other letters in target to see if the letter is in target.
            if match[letter_index] == -1 and word[letter_index] == target[target_letter_index]:
                match[letter_index] = 1
                # If we find the letter in target, replace it with a character so we cannot find it again. Allows use of repeated letters.
                target = target[:target_letter_index] + '-' + target[target_letter_index + 1:]
                break
        # If we don't find a match for the letter, set the match value to 0.
        if match[letter_index] == -1:
            match[letter_index] = 0
    return match


# Function to output a match array as in wordle.
# @param match - a match array with the following values:
# 0=letter not in target, 1=letter in target but wrong position, 2=letter in target and correct position.
def pretty_output(match):
    output = ''
    for i in match:
        if i == 0:
            output += '\U00002B1C'
        elif i == 1:
            output += '\U0001F7E8'
        else:
            output += '\U0001F7E9'
    print(output)

# Function to plot the probability distribution for a word against a given answer set. The more uniform the distribution, the better the word is (generally)
# @param asnwers - list of possible answers.
# @param word - word to calculate probability for.
def plot_probability(answers, word):
    freq = {}
    for target in answers:
        match = tuple(check_word(word, target))
        if match not in freq:
            freq[match] = 0
        freq[match] += 1
    freq = dict(sorted(freq.items(), key = lambda x: x[1], reverse=True))
    fig = go.Figure(data=go.Bar(x=[str(x) for x in list(freq.keys())], y=list(freq.values()))).update_layout(xaxis={'visible': False, 'showticklabels': False})
    fig.show()

# Function to calculate an entropy value for every word in the list of answers.
# @param answers - list of words that are possible answers.
# @returns - sorted dictionary relating each word with its calculated entropy.
def get_entropy(answers):
    entropy_dict = {}
    for target in answers:
        freq = {}
        for word in answers:
            # Get the match array (in an immutable tuple) for the word
            match = tuple(check_word(word, target))
            # Using out match tuple as a key (weird, I know) create a frequency dictionary.
            if match not in freq:
                freq[match] = 0
            freq[match] += 1
        # Sort the dictionary by value, descending.
        freq = dict(sorted(freq.items(), key = lambda x: x[1], reverse=True))
        # Get the overall probabiliy of each occurence based on the number of values in the answer list.
        probability = np.array(list(freq.values())) / len(answers)
        # Calculate entropy using the standard formula.
        entropy = 0
        for p in probability:
            entropy += -p * np.log2(p)
        # Add entropy to a dictionary for each word.
        entropy_dict[target] = entropy
    # Return the sorted entropy dictionary with the highest entropy word at the top.
    return dict(sorted(entropy_dict.items(), key = lambda x: x[1], reverse=True))

# Function to reduce the subspace of an answers list based on a guess.
# @param answers - list of accepted words
# @param guess - word that was guessed.
# @param match_array - match array returned by check_word function.
# @returns - reduced answer space.
def get_subanswers(answers, guess, match_array):
    # Use regex to pull answers with character and positional matches
    regex = ''
    for index in range(5):
        if match_array[index] == 2:
            regex += guess[index]
        else:
            regex += '.'
    subanswers = list(filter(re.compile(regex).match, answers))
    for index in range(5):
        # If we know a character is in the answer, only include answers that contain that character.
        if match_array[index] == 1:
            subanswers = [i for i in subanswers if guess[index] in i and guess[index] != i[index]]
        # If we know a character is not in the answer, remove any words with that character.
        if match_array[index] == 0:
            # In the case that our guess has a repeated letter, only keep answers with one of those letters.
            if guess.count(guess[index]) > 1:
                temp = len([match_array[i] for i in [i for i, ltr in enumerate(guess) if ltr == guess[index]] if match_array[i] != 0])
                subanswers = [word for word in subanswers if word.count(guess[index]) == temp]
                continue
            subanswers = [word for word in subanswers if guess[index] not in word]
    # Remove our original guess from the possible answers.
    if guess in subanswers:
        subanswers.remove(guess)
    return subanswers


# Main function to actually play the game.
# @param answers - the complete list of possible answers.
# @param word - the word we are trying to guess.
# @param initial_entropy - the starting dict of entropies.
def wordle(answers, word, initial_entropy, output=True):
    match = [0, 0, 0, 0, 0]
    count = 0
    while sum(match) != 10:
        if count == 0:
            # Save time by using.
            entropy = initial_entropy
        else:
            # Compute entropy using the current answers space.
            entropy = get_entropy(answers)
        # Pull out the word with the higest entropy. This is our first guess.
        guess = next(iter(entropy))
        # See how good our guess is.
        match = check_word(guess, word)
        # Get the reduced subspace of possible answers.
        answers = get_subanswers(answers, guess, match)
        # Output the results of our guess.
        if output == True:
            pretty_output(match)
        count += 1
    return count

# Function to play every possible game of wordle and return the distribution of number of attempts to win.
# @param answers - list of possible solutions.
# @param entropy - initial entropy dictionary.
def guess_all(answers, entropy):
    rolling_answers = copy.deepcopy(primary_answers)
    rolling_entropy = copy.deepcopy(initial_entropy)
    guess_count = []
    for word in primary_answers:
        print(word)
        guess_count.append(wordle(rolling_answers, word))
        # Cheesy way to increase performance; remove all words that have already been used from the answer space.
        rolling_answers.remove(word)
        rolling_entropy.pop(word)

    fig = go.Figure(data=go.Histogram(x=guess_count))
    fig.show()
    return np.array(guess_count).mean()



num, primary_answers, initial_entropy = open_files()
count = wordle(primary_answers, primary_answers[num], initial_entropy, False)
print('Wordle ' + str(num - 1) + ' ' + str(count) + '/6')
count = wordle(primary_answers, primary_answers[num], initial_entropy)
num += 1
store_answers(num, primary_answers)
