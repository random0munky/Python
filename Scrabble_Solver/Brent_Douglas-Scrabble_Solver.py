#!/usr/local/bin/python3

######################################################################
__author__ = "Brent Douglas"
__version__ = "1.0"
__maintainer__ = "Brent Douglas"
__email__ = "brent.douglas.j@gmail.com"
__status__ = "Development"
__date__ = "April 04 2018"
__dependencies__ = "Readme.txt, scrabble_score.txt, wordsEn.txt"
__libraries__ = "itertools"
__python_version__ = "3.6.5"
######################################################################


from itertools import permutations

# Create a list to encapsulate the contents of wordsEn.txt which houses all
# the legal words that can be accepted in Scrabble
class ImportWords(object):
    def list_words(self):
        wordsEn = []
        input_file = open('wordsEn.txt', 'r')
        for line in input_file:
            word = line.rstrip('\n')
            wordsEn.append(word)
        input_file.close()
        return wordsEn

class UserInput(object):
    # Permutate the user input into a list variable
    # Output only the permutations that are in the
    # wordsEn list
    def perm_string(self, word_input, wordsEn):
        perms_list = []
        words_list = []

        for i in range(len(word_input)):
            perms_list.extend([''.join(x) for x in permutations(word_input, i + 1)])

        for perm in perms_list:
            if perm in wordsEn:
                words_list.append(perm)
            else:
                pass
        return words_list

    # Compute the Scrabble score for the user inputted word
    # Reading from text file named scrabble_score.txt
    # which contain all the scores for each of the letters
    # In addition, take in the permutations of the inputted
    # word and sort the score from highest to lowest as well
    def compute_score(self, word_input, perms):
        scrabble_scoring = {}
        input_file = open('scrabble_score.txt', 'r')
        for line in input_file:
            line = line.rstrip('\n')
            line = line.strip()
            num, letters = line.split('|', 1)
            letters = letters.split(',')
            for letter in letters:
                scrabble_scoring[letter.strip().lower()] = num.strip()

        # Check to see if the inputted word is an actual
        # scrabble word
        input_file.close()
        wordIsReal = False
        for perm in perms:
            if word_input == perm:
                wordIsReal = True

        # Proceed to get score for word_input if
        # wordIsReal = True. If not true, set
        # scrabble_score = 0
        input_scrabble_score = 0
        if wordIsReal == True:
            # Get score for typed in word
            char_input = list(word_input)

            # For each char from char_input, go through
            # scrabble_scoring to determine point value
            for char in char_input:
                score = scrabble_scoring.get(char)
                input_scrabble_score += int(score)
        else:
            input_scrabble_score = 0

        # Get scores and sort the available permutations of the
        # typed in word (word, score)
        perm_scores = []
        for perm in perms:
            perm_input = list(perm)
            perm_scrabble_score = 0
            for char in perm:
                score = scrabble_scoring.get(char)
                perm_scrabble_score += int(score)
            perm_scores.append([perm_scrabble_score, perm])
        perm_scores = sorted(perm_scores, reverse=True)
        perm_scores = [x[1] for x in perm_scores] # Removes first x[0] in tuple
        perm_scores = '\n'.join(perm_scores) # Adds a new-line after each tuple

        return input_scrabble_score, perm_scores

def main():
    # Input var will take in what the user will type in
    word_input = input("Enter the word to get your Scrabble score: ")
    word_input = word_input.lower() # Making sure the input is lowercase
    
    words_method = ImportWords()
    wordsEn = words_method.list_words()
    
    userInput_method = UserInput()
    word_permutations = userInput_method.perm_string(word_input, wordsEn)
    score, perm_scores = userInput_method.compute_score(word_input, word_permutations)

    print ("This is the inputted word:\n%s" % (word_input,))
    print ("These are the permutations for said inputted word:\n%s" % (perm_scores, ))
    print ("This is the scrabble score for %s:\n%s" % (word_input, score,))

if __name__ == '__main__':
    main()

