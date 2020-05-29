import requests
import urllib.parse
import json
import sys
import re


from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL
from random import *


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///storage.db")


def tokenizeChar(words, wordToTokenize):
    """Tokenizes puncutation by ensuring that there is a space before and after each punctuation symbol"""
    words = words.replace(wordToTokenize, " " + wordToTokenize + " ")
    return words


def tokenizePunctuation(words):
    """Tokenizes a string, returns the tokenized and cleaned up string"""
    # New lines are removed to reduce risk of error
    words = words.replace('\n', ' ')

    # Certain punctuation is tokenized to be added
    # into our database
    toTokenize = ",.!?"
    for c in toTokenize:
        words = tokenizeChar(words, c)

    # Certain punctuation marks (that are difficult to properly
    # implement) are removed for the time being.
    toRemove = "()\"{}[]"
    for c in toRemove:
        words = words.replace(c, '')

    # Removing extra spaces from string to keep the words.split in
    # application.py working properly
    # From: https://stackoverflow.com/questions/42357021/how-to-remove-extra-spaces-in-a-string
    words = re.sub(r' +', ' ', words)

    return words


def decapitalizeWords(tokenized):
    """Decapitalize all strings in a list"""
    for num in range(len(tokenized) - 1):
        # Check if a string is upper: https://stackoverflow.com/questions/8222855/check-if-string-is-upper-lower-or-mixed-case-in-python
        if tokenized[num].isupper():
            # Convert a string to lower: https://stackoverflow.com/questions/6797984/how-to-lowercase-a-string-in-python
            tokenized[num] = tokenized[num].lower()
    return tokenized


def decondenser(word):
    """Takes the condensed text and decondenses it into a list"""
    text = db.execute("SELECT next FROM words WHERE word=:word", word=word)
    tokenized = text[0]['next'].split('§')

    # If no next word is found, return a conjunctioin instead
    if(text[0]['next'] == ''):
        return getConjunction()
    else:
        return tokenized


def condenser(thisList, keyWord):
    """Turn a list into a large string to be inputted in the database as text"""

    # Initializing a string
    reallyBigString = ''

    for word in thisList:
        reallyBigString = reallyBigString + "§" + word

    # check if the word is already in the database; if it is then decondense what is already in the database
    # then add reallybigstring to it, and insert it back in
    # if it does not already exist, then make a new row in the database
    thisWord = db.execute("SELECT next FROM words WHERE word =:keyWord", keyWord=keyWord)
    if not thisWord:
        db.execute("INSERT INTO words (word, next) VALUES (:word, :nextWords)", word=keyWord, nextWords=reallyBigString)
    else:
        oldWords = db.execute("SELECT next FROM words WHERE word=:word", word=keyWord)
        newWords = str(reallyBigString + oldWords[0]['next'])
        db.execute("UPDATE words SET next=:nextWords WHERE word=:keyWord", nextWords=newWords, keyWord=keyWord)


def randomWords(numberOfWords, startingWord):
    """Returns randomly generated text depending on the starting word and the number of words to be generated"""

    # Create a list of possible words using a startingWord
    possibleWords = decondenser(startingWord)

    # Initialize outputString as an empty string
    outputString = ""

    # Pick a random word from the decondensed list
    # Random number generator: https://pythonspot.com/random-numbers/
    for num in range(numberOfWords):

        # Chooses a random number from 0 to the 0-indexed size of the list
        randomNumber = randint(0, len(possibleWords) - 1)

        # Picks a word in the list randomly using the random number
        thisWord = possibleWords[randomNumber]

        # Doesn't make a space before if the "word" is a punctuation mark
        if (thisWord == "." or thisWord == "," or thisWord == "!" or thisWord == "?"):
            outputString = outputString + thisWord
        else:
            outputString = outputString + " " + thisWord

        # Get a list of possible words for the newly generated word
        possibleWords = decondenser(possibleWords[randomNumber])

    return outputString

# Returns a conjunction to be used
# When a word does not have a next
# word in the database


def getConjunction():
    """Returns a conjunction to be used when a word doesn't have a next word in the database"""
    conjunctions = ['and', 'but', 'yet', 'also']
    return conjunctions


def installText(words):
    """Installs text into the databse to be used later"""
    # Global variable number
    # global number
    # number = request.form.get("number")

    # Ensures that the words "and" and "time" are in the database as they're necessary for function
    testTime = db.execute("SELECT next FROM words WHERE word=:word", word="time")
    if not testTime:
        db.execute("INSERT INTO words (word, next) VALUES (:word, :nextWords)", word="time", nextWords="§the")
    testCon = db.execute("SELECT next FROM words WHERE word=:word", word="and")
    if not testCon:
        testCon = db.execute("SELECT next FROM words WHERE word=:word", word="yet")
    if not testCon:
        testAnd = db.execute("SELECT next FROM words WHERE word=:word", word="but")
    if not testCon:
        testAnd = db.execute("SELECT next FROM words WHERE word=:word", word="also")
    if not testCon:
        db.execute("INSERT INTO words (word, next) VALUES (:word, :nextWords)", word="and", nextWords="§the")
        db.execute("INSERT INTO words (word, next) VALUES (:word, :nextWords)", word="yet", nextWords="§the")
        db.execute("INSERT INTO words (word, next) VALUES (:word, :nextWords)", word="but", nextWords="§the")
        db.execute("INSERT INTO words (word, next) VALUES (:word, :nextWords)", word="also", nextWords="§the")

    # Tokenizes punctuation to make it easier to store punctuation in the markov chain
    words = tokenizePunctuation(words)

    # Tokenize string: https://www.geeksforgeeks.org/python-string-split/
    tokenizedWords = words.split(' ')

    # Converts all words to lowercase
    tokenizedWords = decapitalizeWords(tokenizedWords)

    # Initializes a list to store tokens in
    uniqueWords = list()

    # Making a new list with unique words
    for tokenizedWord in tokenizedWords:

        if tokenizedWord not in uniqueWords:
            uniqueWords.append(tokenizedWord)

    # Compiling a list of following words per unique word; add to SQL database
    for uniqueWord in uniqueWords:
        # Find where uniqueWord == tokenizedWord, add the following word to a list
        wordsForDatabase = list()
        for num in range(len(tokenizedWords) - 1):
            if uniqueWord == tokenizedWords[num]:
                wordsForDatabase.append(tokenizedWords[num + 1])

        condenser(wordsForDatabase, uniqueWord)


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code
