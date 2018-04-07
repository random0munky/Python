#!/usr/local/bin/python3

######################################################################
__author__ = "Brent Douglas"
__version__ = "1.0"
__maintainer__ = "Brent Douglas"
__email__ = "brent.douglas.j@gmail.com"
__status__ = "Development"
__date__ = "April 04 2018"
__dependencies__ = "Readme.txt, scrabble_score.txt, wordsEn.txt"
__libraries__ = "itertools, unittest"
__python_version__ = "3.6.5"
######################################################################

import unittest
from itertools import permutations

# Test to see if the Scrabble legal words are added to the array
class ImportWords(unittest.TestCase):
    def test_list_words(self):
        print ('test_list_words')
        wordsEn = []
        input_file = open('wordsEn.txt', 'r')
        for line in input_file:
            word = line.rstrip('\n')
            wordsEn.append(word)
        input_file.close()
        self.assertTrue(wordsEn)
        return wordsEn
        
# Test to see if permutations of the user input into a
# list variable outputs only the permutations that are in
# the wordsEn list
class UserInput(unittest.TestCase):
    def setUp(self):
        print ('setUp')
        self.expected_perms_list = ['hat', 'ah', 'ha', 'th', 'at', 'a']
        self.word_input = "hat"
        self.wordsEn = ImportWords.test_list_words(self)
        self.word_input_score = 6
        self.expected_perm_scores = [[6, 'hat'], [5, 'ha'],[5, 'ah'], [5, 'th'], [2, 'at'], [1, 'a']]
        
    def test_perm_string(self):
        print ('test_perm_string')
        perms_list = []
        words_list = []
        
        for i in range(len(self.word_input)):
            perms_list.extend([''.join(x) for x in permutations(self.word_input, i + 1)])
            
        for perm in perms_list:
            if perm in self.wordsEn:
                words_list.append(perm)
            else:
                pass
            
        # Test check if the values in expected_perms_list are in 
        # perms_list as well as perms_list are in expected_perms_list
        self.assertCountEqual(words_list, self.expected_perms_list, msg="Permutation arrays do not equal each other")
        
        return words_list
        
    def test_compute_score(self):
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
        wordIsReal = False
        for perm in self.expected_perms_list:
            if self.word_input == perm:
                wordIsReal = True

        # Proceed to get score for word_input if
        # wordIsReal = True. If not true, set
        # scrabble_score = 0
        input_scrabble_score = 0
        if wordIsReal == True:
            # Get score for typed in word
            char_input = list(self.word_input)

            # For each char from char_input, go through
            # scrabble_scoring to determine point value
            for char in char_input:
                score = scrabble_scoring.get(char)
                input_scrabble_score += int(score)
        else:
            input_scrabble_score = 0

        # Test to make sure the word_input score is the same as the input_scrabble_score
        self.assertEqual(self.word_input_score, input_scrabble_score)
        
        # Get scores and sort the available permutations of the
        # typed in word (word, score)
        perm_scores = []
        for perm in self.expected_perms_list:
            perm_input = list(perm)
            perm_scrabble_score = 0
            for char in perm:
                score = scrabble_scoring.get(char)
                perm_scrabble_score += int(score)
            perm_scores.append([perm_scrabble_score, perm])
        perm_scores = sorted(perm_scores, reverse=True)
        
        # Test to make sure perm_scores is the same as expected_perm_scores
        self.assertCountEqual(perm_scores, self.expected_perm_scores, msg="Permutation scores and expected permutation scores are not equal")
        
        perm_scores = [x[1] for x in perm_scores] # Removes first x[0] in tuple
        perm_scores = '\n'.join(perm_scores) # Adds a new-line after each tuple
        
        input_file.close()

        return input_scrabble_score, perm_scores
    
    
    
    
if __name__ == '__main__':
    unittest.main()