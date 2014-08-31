#!/usr/bin/python
# -*- coding: utf-8 -*-

#Mohamed Abdalkader
#Basic SA application
#oct 18

import re
import codecs
from nltk.tokenize import word_tokenize, wordpunct_tokenize, sent_tokenize
import csv
import nltk
from nltk import ISRIStemmer

def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]
        
class SA:
    def __init__(self):
        self.setWeightedLexicon("weightedLexicon.csv")
        self.setUnweightedLexicon("sentimentLexiconUTF8.csv")

    def lookUpWordScore(self, word, lexicon, use_lemma):
        stemmer = ISRIStemmer()
        for key in lexicon.iterkeys():
            if key == word:
                return lexicon[key]
        for key in lexicon.iterkeys():
            if stemmer.stem(key) == stemmer.stem(word):
                print word
                print key
                return lexicon[key]*0.25
        for key in lexicon.iterkeys():
            med = nltk.metrics.edit_distance(word, key)
            match = 1 - (float(med)/len(word))
            if match > 0.7:
                return lexicon[key]*0.25
        return 0

    def calculate_dp_score(self, wordScore):
        dpScore = 0
        if wordScore > 0:
            dpScore = -1*(1-wordScore)
        elif wordScore < 0:
            dpScore = 1 + wordScore
        else:
            dpScore = 0
        return dpScore


    def analyze_composite(self, sentence, weightedLexicon):
        if weightedLexicon:
            lexicon = self.weightedLexicon
        else:
            lexicon = self.unweightedLexicon

        tweetScore = 0
        words =wordpunct_tokenize(sentence)
        
        for index, word in enumerate(words):
            term = word
            if len(words[index:]) < 6:
                maxim = index + len(words[index:])-1
            else:
                maxim = index + 5
            for i in range(index+1, maxim + 1):
                term = term + " " + words[i]
                #print term + ":" + str(self.lookUpWordScore(term, lexicon))
                tweetScore = tweetScore + self.lookUpWordScore(term, lexicon, False)
            
        return tweetScore

    def analyze(self, sentence, weightedLexicon, details):

        if weightedLexicon:
            lexicon = self.weightedLexicon
        else:
            lexicon = self.unweightedLexicon

        out = ""
        tweetScore = 0
        words =wordpunct_tokenize(sentence)
        #words = sentence.split()
        compositeScore = 0#self.analyze_composite(sentence, lexicon)

        for word in words:
           
            wordScore = self.lookUpWordScore(word, lexicon, True)
                        
            if details:
                print  word + ":" +  str(wordScore) + "\n"
            
            out = out +  word + ":".encode('utf8') +  str(wordScore).encode('utf8') + "\n"
            tweetScore = tweetScore + wordScore
        
        tweetScore = tweetScore + compositeScore
        
        if details:
            print "tweetScore: " + str(tweetScore)
        
        out = out + "---------".encode('utf8')
        return [tweetScore, out]
                

    def setWeightedLexicon(self, lexiconFile):
        self.weightedLexicon = {}
        with open(lexiconFile, 'rb') as f:
            reader = unicode_csv_reader(f)
            for row in reader:
                word = row[0]
                rawScore = float(row[2])
                if row[1] == "neg":
                    score = -rawScore
                elif row[1] == "pos":
                    score = rawScore
                else:
                    print "unexpected value while parsing the lexicon"
                    return
                self.weightedLexicon[word] = score

    def setUnweightedLexicon(self, lexiconFile):
        self.unweightedLexicon = {}
        with open(lexiconFile, 'rb') as f:
            reader = unicode_csv_reader(f)
            for row in reader:
                word = row[0].strip()
                if row[1] == "1":
                    self.unweightedLexicon[word] = 1
                elif row[1] == "-1":
                    self.unweightedLexicon[word] = -1
                else:
                    print "unexpected value while parsing the lexicon"
                    return

    def evaluate(self, dataSetFile, write, writeMisses, detailedTweets, doublePolarity):
        
        missesFile= codecs.open(dataSetFile[0:-4]+"Misses-1.csv","w","utf-8")

        if write:
            evaluationFile = codecs.open(dataSetFile[0:-4]+"Evaluated-1.csv","w","utf-8")
            headers = "TweetNumber,Tweet,correctScore,GivenScore\n".encode('utf8')
            evaluationFile.write(headers)

        numberOfTweets = 0

        unscored = 0
        misses = 0

        positive = 0
        negative = 0
        neutral = 0

        pg = 0
        pn = 0
        
        gp = 0
        gn = 0
        
        np = 0
        ng = 0
        


        with open(dataSetFile, 'rb') as f:
            reader = unicode_csv_reader(f)
            for row in reader:
                
                tweet= row[0]
                print tweet
                correctScore = float(row[1])                            

                numberOfTweets = numberOfTweets + 1
                if doublePolarity:
                    scoreAndOut = self.analyze(tweet, True, False)
                else:
                    scoreAndOut = self.analyze(tweet, True, False)

                score = scoreAndOut[0]
                out = scoreAndOut[1]

                if numberOfTweets in detailedTweets:
                    print out

                
                if score > 0:
                
                    score = 1
                    positive = positive + 1

                elif score == 0:
                    
                    score = 0
                    neutral = neutral + 1

                elif score < 0:
                    
                    score = -1
                    negative = negative + 1

                else:
                    print "invalid score"
                    return


                #mistakes details
                if correctScore == 1 and score == -1:
                    pg = pg + 1
                elif correctScore == 1 and score == 0:
                    pn = pn + 1
 #                   self.analyze(tweet, True, True, False)
                elif correctScore == 0 and score == 1:
                    np = np + 1
                elif correctScore == 0 and score == -1:
                    ng = ng  + 1
                elif correctScore == -1 and score == 1:
                    gp = gp + 1
                elif correctScore == -1 and score ==0:
                    gn = gn + 1
#                    self.analyze(tweet, True, True, False)


                #evaluationFile.write(tweet+","+ str(correctScore).encode('utf8')+","+ str(score).encode('utf8')+"\n")
                if score != correctScore:
                    misses = misses + 1
                    if write:
                        evaluationFile.write(str(numberOfTweets).encode('utf8') + "," + tweet+","+ str(correctScore).encode('utf8')+","+ str(score).encode('utf8')+"\n")
                   #if writeMisses:
                   #     missesFile.write(out)

            if write:
                evaluationFile.close()
            missesFile.close()

            print "misses: " + str(misses)
            print "accuracy: " +str((numberOfTweets - misses)/float(numberOfTweets))
            
            
            print ""

            print "positive: " + str(positive)
            print "negative: " + str(negative)
            print "neutral: " + str(neutral)

            print ""

            print "Expected Positive Got Negative: " + str(pg)
            print "Expected Positive Got Neutral:  " + str(pn)
            
            print ""

            print "Expected Neutral Got Positive:  " + str(np)
            print "Expected Neutral Got Negative:  " + str(ng)

            print ""

            print "Expected Negative Got Neutral:  " + str(gn)
            print "Expected Negative Got Positive: " + str(gp)
    def printArabic(self, stringToPrint):
        print unicode(stringToPrint, 'utf-8')


analyzer = SA()
#print analyzer.analyze(u'', True, True)
#analyzer.evaluate("datasets/Eval500.csv", True, True, [], False)
analyzer.evaluate("datasets/Eval1200.csv", True, True, [], False)
