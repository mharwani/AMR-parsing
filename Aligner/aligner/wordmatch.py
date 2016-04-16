# -*- coding: utf-8 -*-
"""
Created on Sun Mar 20 06:41:41 2016

@author: mrudul
"""

from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer

import re



#Check if token is a word
def isWord(token):
    if re.match('[a-zA-Z\d]+', token):
        return True
    return False
    
    
#Generate wordnet lemmas from tokens
def getlemmas(tokens):
    lemmas = []
    for token in tokens:
        if len(token) < 2 or not isWord(token) or token == "the":
            lemmas.append({})
            continue
        
        tokenLemmas = {}
        #Synonyms
        for syn in wn.synsets(token):
            #Derived Forms and their Syns
            for lemma in syn.lemmas():
                for df in lemma.derivationally_related_forms():
                    for ln in df.synset().lemma_names():
                        tokenLemmas[ln] = 4
                    tokenLemmas[df.name()] = 3
            for lname in syn.lemma_names():
                tokenLemmas[lname] = 2
        
        #Wordnet lemmas
        l = WordNetLemmatizer()
        for x in ('v','a','s','r','n'):
            tmp = l.lemmatize(token, x)
            tokenLemmas[tmp] = 1
            tmp = l.lemmatize(tmp, x)
            tokenLemmas[tmp] = 1
        
        #Exact
        tokenLemmas[token] = 1
        
        lemmas.append(tokenLemmas)
    
    return lemmas
    

#Search exact keywords against tokens. Returns spans of matching tokens
def search_exact(words, tokens):
    i = 0
    n = len(tokens)
    m = len(words)
    n2 = n - m + 1
    words = [x.lower() for x in words]
    idxs = []
    while i < n2:
        if words[0] in tokens[i]:
            start = i
            k = 1
            i += 1
            while k < m and i < n:
                if words[k] not in tokens[i]:
                    if tokens[i] == 'the' or not isWord(tokens[i]):
                        i += 1
                        continue
                    else:
                        break
                k += 1
                i += 1
            if k == m:
                idxs.append((start, i))
            continue
        i += 1
    return idxs
    

#Longest common subsequence
def lc_seq(X, Y, L=[]):
    n = len(X)
    m = len(Y)
    
    if not L:    
        L.append([0]*(n+1))
    k = len(L) - 1
    
    for i in range(1, m+1):
        L.append([0]*(n+1))
        idx = k+i
        for j in range(n+1):
            if j == 0:
                L[idx][j] = 0
            elif X[j-1] == Y[i-1]:
                L[idx][j] = L[idx-1][j-1] + 1
            else:
                L[idx][j] = max(L[idx-1][j], L[idx][j-1])
    
    return L[m+k][n]


#Longest common substring
def lc_str(X, Y):
    n = len(X)
    m = len(Y)
    L = [[0]*(n+1) for i in range(m+1)]
    l = 0
    
    for i in range(1, m+1):
        for j in range(1, n+1):
            if Y[i-1] == X[j-1]:
                L[i][j] = L[i-1][j-1] + 1
                if L[i][j] > l:
                    l = L[i][j]
            else:
                L[i][j] = 0
    
    return l
    

#Fuzzy match
def fuzzy(X, Y, thres=None):
    l = lc_str(X, Y)
    if thres:
        if type(thres) is float:
            fl = float(l)
            lx, ly = len(X), len(Y)
            if fl/max(lx,ly) >= thres:
                return True
            else:
                return False
        if type(thres) is int:
            if l >= thres:
                return True
            else:
                return X == Y
    else:
        return X == Y


#Fuzzy search
def search_fuzzy(words, tokens, thres=4):
    idxs = []
    n = len(tokens)
    
    for i in range(n):
        for word in words:
            if fuzzy(word, tokens[i], thres) or (len(word) > 2 and word == tokens[i][:-1]):
                idxs.append((i, i+1))
                break
    
    return idxs
    

#Fuzzy match with longest common subsequence
def search_subseq(word, tokens, thres=0.7):
    idxs = []
    probs = []
    n = len(tokens)
    m = len(word)
    maxsofar = thres
    
    for i in range(n):
        L = []
        token = tokens[i]
        toklen = len(token)
        maxlength = max(m, toklen)
        maxseq = lc_seq(word, token, L)
        maxprob = maxseq/maxlength
        maxj = i
        for j in range(i+1, n):
            if maxseq == m or m/maxlength < thres:
                break
            token = tokens[j]
            toklen += len(token)
            if toklen > maxlength:
                maxlength = toklen
            seq = lc_seq(word, token, L)
            prob = seq/maxlength
            if prob > maxprob:
                maxprob = prob
                maxj = j
                maxseq = seq
            elif seq > maxseq:
                maxseq = seq
        if maxprob > maxsofar:
            idxs = [(i, maxj+1)]
            probs = [maxprob]
            maxsofar = maxprob
        elif maxprob == maxsofar:
            idxs.append((i, maxj+1))
            probs.append(maxprob)
    
    return idxs, probs   
    

#Search strings character by character
def search_literal(words, tokens):
    i = 0
    n = len(tokens)
    m = len(words)
    idxs = []
    while i < n:
        try:
            words[0][0]
            tokens[i][0]
        except IndexError:
            print("i = " + str(i))
            print("word: " + words[0])
            print("token: " + tokens[i])
        if words[0][0] == tokens[i][0]:
            indw = indt = 0
            start = i
            cur_word = 0
            wordlen = len(words[0])
            toklen = len(tokens[i])
            while cur_word < m and i < n:
                if words[cur_word][indw] != tokens[i][indt]:
                    break
                indw += 1
                indt += 1
                if indw == wordlen:
                    indw = 0
                    cur_word += 1
                    if cur_word != m:
                        wordlen = len(words[cur_word])
                if indt == toklen:
                    indt = 0
                    i += 1
                    if cur_word < m and words[cur_word] != "the":
                        while i < n and tokens[i] == "the":
                            i += 1
                    if i != n:
                        toklen = len(tokens[i])
            if cur_word == m:
                end = i
                if indt != 0:
                    end = i+1
                idxs.append((start, end))
        i += 1
    return idxs
    

#Extend interval to match one of nearest names
def near(names, tokens, start, end):
    i = start - 1
    if i >= 0:
        if tokens[i] in names:
            return (i, end)
        elif len(tokens[i]) < 3:
            i -= 1
            if i >= 0 and tokens[i] in names:
                return (i, end)
    i = end
    n = len(tokens)
    if i < n:
        if tokens[i] in names:
            return (start, i+1)
        elif len(tokens[i]) < 3:
            i += 1
            if i < n and tokens[i] in names:
                return (start, i+1)
    return (start, end)
    

#Search keywords against token lemmas from wordnet. Returns indexes of matching tokens
def search_wordnet(word, lemmas):
    minS = 10
    idxs = []
    probs = []
    n = len(lemmas)
    for i in range(n):
        if word in lemmas[i]:
            score = lemmas[i][word]
            idxs.append((i, i+1))
            probs.append(1/score)
    return (idxs, probs)
    

#Search for person
def search_person(tokens):
    idxs = []
    n = len(tokens)
    for i in range(n):
        if tokens[i] in ["person", "persons", "people"]:
            idxs.append((i, i+1))
    return idxs