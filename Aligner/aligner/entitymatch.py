# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 04:41:52 2016

@author: mrudul
"""

import os
import csv
from .Objects import AMRNode
from . import wordmatch
import re



#Month table
_months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
months = {}
for idx, word in enumerate(_months):
    months[word] = idx+1
    months[word[0:3]] = idx+1
    months[word[0:3]+'.'] = idx+1
months["sept"] = 9
months["sept."] = 9
del _months


#Weekdays
weekdays = {'monday':['mon'], 'tuesday':['tues', 'tue'], 'wednesday':['wed'], 'thursday':['thurs', 'thu'], 'friday':['fri'], 'saturday':['sat'], 'sunday':['sun']}


#Decades
decades = ["", "", "twenties", "thirties", "forties", "fifties", "sixties", "seventies", "eighties", "nineties"]


#Days
ordinals = [
        "", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
        "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth",
        "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth"
      ]


#Nationalities
nations = []
cur_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(cur_path, "nationalities.txt")
with open(file_path) as csvfile:
    csvfile.seek(0)
    reader = csv.reader(csvfile, delimiter='\t')
    for row in reader:
        n = len(row)
        names = row[0].lower().strip().split("/")
        for i in range(1,n):
            names2 = row[i].lower().strip().split("/")
            for name in names2:
                if not name:
                    continue
                if name not in names:
                    names.append(name)
        nations.append(names)


#Find word spans matching a nation
def find_nation(names, tokens):
    idxs = []
    words = [names]
    name = ' '.join(names)
    for nat in nations:
        if name in nat:
            for n in nat:
                words.append(n.split())
    words = sorted(words, key=lambda word: len(word), reverse=True)
    m = len(words)
    n = len(tokens)
    i = 0
    probs = []
    while i < n:
        for j in range(m):
            if words[j][0] in tokens[i]:
                p = len(words[j][0])/len(tokens[i])
                k = len(words[j])
                l = 1
                i2 = i+1
                while i2 < n and l < k:
                    if words[j][l] not in tokens[i2]:
                        break
                    p += len(words[j][l])/len(tokens[i2])
                    i2 += 1
                    l += 1
                if l == k:
                    idxs.append((i, i2))
                    probs.append(p)
                    i += k-1
                    break
        i += 1
    return idxs, probs


#Find word spans matching a month
def find_month(month, tokens):
    idxs = []
    n = len(tokens)
    for i in range(n):
        token = tokens[i]
        if str(month) in token:
            idxs.append((i, i+1))
        
        elif token.isdigit():
            if int(token) == month:
                idxs.append((i, i+1))
                
        elif '/' in token:
            nums = token.split('/')
            if len(nums) < 4 and all([num.isdigit() for num in nums]):
                for num in nums:
                    if int(num) == month:
                        idxs.append((i, i+1))
                        break
                
        elif token in months and months[token] == month:
            idxs.append((i, i+1))
    
    return idxs
    

#Find word spans matching a day
def find_day(day, tokens):
    n = len(tokens)
    idxs = []
    i = 0
    while i < n:
        token = tokens[i]
        if str(day) in token:
            idxs.append((i, i+1))
            
        elif token.isdigit():
            if int(token) == day:
                idxs.append((i, i+1))
        
        elif '/' in token:
            nums = token.split('/')
            if len(nums) < 4 and all([num.isdigit() for num in nums]):
                for num in nums:
                    if int(num) == day:
                        idxs.append((i, i+1))
                        break
            
        elif day < 21:
            if token == ordinals[day]:
                idxs.append((i, i+1))
                
        elif day < 30:
            if token == "twenty":
                i += 1
                rem = day - 20
                if i < n: 
                    if tokens[i] == ordinals[rem]:
                        idxs.append((i-1, i+1))
                    elif tokens[i] == '-':
                        i += 1
                        if i < n and tokens[i] == ordinals[rem]:
                            idxs.append((i-2, i+1))
                            
        elif day == 30:
            if token == "thirtieth":
                idxs.append((i, i+1))
                
        elif token == "thirty" and i < n-1:
            i += 1
            if tokens[i] == "first":
                idxs.append((i-1, i+1))
            elif tokens[i] == '-':
                i += 1
                if i < n and tokens[i] == "first":
                    idxs.append((i-2, i+1))
                    
        i += 1
    
    return idxs
        
    

#Find word spans matching a year
def find_year(year, tokens):
    idxs = []
    n = len(tokens)
    for i in range(n):
        token = tokens[i]
        if year in token:
            idxs.append((i, i+1))
            
        elif year[2:] in token:
            idxs.append((i, i+1))
                
        elif '/' in token:
            nums = token.split('/')
            if len(nums) < 4 and all([num.isdigit() for num in nums]):
                for num in nums:
                    if num == year or (year[:2] == '20' and year[2:] == num):
                        idxs.append((i, i+1))
                        break
                
    return idxs


#Find word spans matching a decade
def find_decade(dec, tokens):
    idxs = []
    n = len(tokens)
    for i in range(n):
        token = tokens[i]
        if token == dec or (token == dec[2:] and dec[:2] == '19'):
            if i < n-1 and tokens[i+1] == '\'s':
                idxs.append((i, i+1))
                
        elif token[-1] == 's':
            if token[:-1] == dec:
                idxs.append((i, i+1))
            elif dec[:2] == '19':
                if token[:-1] == dec[2:]:
                    idxs.append((i, i+1))
                elif token == decades[int(dec[2])]:
                    idxs.append((i, i+1))
    
    return idxs


#Find word spans matching a week day
def find_weekday(name, tokens):
    idxs = []
    n = len(tokens)
    names = [name]
    for k in weekdays[name]:
        names.append(k)
    
    for i in range(n):
        if tokens[i] in names or (tokens[i][-1] == 's' and tokens[i][:-1] in names):
            idxs.append((i, i+1))
    
    return idxs
    

#Find word spans matching a century
def find_cent(cent, tokens):
    n = len(tokens)
    idxs = []
    i = 0
    while i < n:
        token = tokens[i]
        if token.isdigit():
            if int(token) == cent or int(token) == cent*100:
                start, end = wordmatch.near(["century"], tokens, i, i+1)
                idxs.append((start, end))
                i = end - 1
                    
        elif len(token) > 2 and \
        token[-2:] in ('st','nd','rd','th') and \
        token[:-2].isdigit() and \
        int(token[:-2]) == cent:
            start, end = wordmatch.near(["century"], tokens, i, i+1)
            idxs.append((start, end))
            i = end - 1
                
        elif cent < 21 and token == ordinals[cent]:
            start, end = wordmatch.near(["century"], tokens, i, i+1)
            idxs.append((start, end))
            i = end - 1
        
        elif cent == 21 and token == "twenty" and i < n-1:
            i += 1
            if tokens[i] == "first":
                idxs.append((i-1, i+1))
            elif tokens[i] == '-':
                i += 1
                if i < n and tokens[i] == "first":
                    idxs.append((i-2, i+1))
                
        i += 1
        
    return idxs


#Find word spans matching a time
def find_time(time, tokens):
    idxs = []
    n = len(tokens)
    times = time.split(':')
    hour = int(times[0])
    minute = int(times[1])
    k = len(times)
    for i in range(n):
        token = tokens[i]
        if token == time:
            idxs.append((i, i+1))
                    
        elif token.isdigit() and minute == 0:
            val = int(token)
            if i < n-1:
                if tokens[i+1] in ('am','a.m.','a.m'):
                    if val == 12 and hour == 0:
                        idxs.append((i, i+2))
                        continue
                    elif val == hour:
                        idxs.append((i, i+2))
                        continue
                elif tokens[i+1] in ('pm','p.m.','p.m'):
                    if val == 12 and hour == 12:
                        idxs.append((i, i+2))
                        continue
                    elif val == hour-12:
                        idxs.append((i, i+2))
                        continue
                elif tokens[i+1] == "o\'clock" and val == hour:
                    idxs.append((i, i+2))
                    continue
            if val == hour:
                idxs.append((i, i+1))
            elif len(token) == 4 and int(token[:2]) == hour and int(token[2:]) == 0:
                idxs.append((i, i+1))
                
        elif token.isdigit():
            if len(token) == 4 and k == 2:
                if int(token[:2]) == hour and int(token[2:]) == minute:
                    idxs.append((i, i+1))
            elif len(token) == 6 and k == 3:
                if int(token[:2]) == hour and int(token[2:4]) == minute and int(token[4:]) == int(times[2]):
                    idxs.append((i, i+1))
        
        elif hour == 0 and minute == 0 and token == "midnight":
            idxs.append((i, i+1))
        
        elif len(token) > 2:
            if token[-2:] == 'am':
                val = int(token[:-2])
                if val == 12 and hour == 0:
                    idxs.append((i, i+1))
                elif val == hour:
                    idxs.append((i, i+1))
            elif token[-2:] == 'pm':
                val = int(token[:-2])
                if val == 12 and hour == 12:
                    idxs.append((i, i+1))
                elif vall == hour-12:
                    idxs.append((i, i+1))
                
    return idxs


#Align node entities
def align(nodes, tokens, alg):
    for nodeid, node in nodes.items():
        if nodeid in alg:
            continue
        name = node.inst
    
        #Named entities
        if "name" in node.child:
            nodes_name = node.child["name"]
            aligned = False
            for node_name in nodes_name:
                if node_name.id not in alg:
                    i = 1
                    words = []
                    link = "op" + str(1)
                    while link in node_name.child:
                        vals = re.split(r'([-]+)', node_name.child[link][0].lower()[1:-1])
                        for val in vals:
                            if val:
                                words.append(val)
                        i += 1
                        link = "op" + str(i)
                    numlinks = i
                    if words:
                        if name in ("country", "nation"):
                            idxs, probs = find_nation(words, tokens)
                        else:
                            idxs, probs = wordmatch.search_subseq("".join(words), tokens)
                        if idxs:
                            alg[node_name.id] = (idxs, probs)
                            for l in range(1,numlinks):
                                key = "op" + str(l)
                                val = node_name.child[key][0]
                                alg[node_name.id, key, val] = (idxs, probs)
                            aligned = True
                    
            #if aligned:
            #   alg[nodeid] = alg[node_name.id]
                
            continue
        
        #Date entities
        if name == "date-entity":
            #Month, day, year, ...
            if "month" in node.child:
                try:
                    val = node.child["month"][0]              
                    month = int(val)
                    idxs = find_month(month, tokens)
                    if idxs:
                        alg[nodeid, "month", val] = (idxs, [1] * len(idxs))
                except ValueError:
                    "Do nothing"
                    
            if "day" in node.child:
                try:
                    val = node.child["day"][0]
                    day = int(val)
                    idxs = find_day(day, tokens)
                    if idxs:
                        alg[nodeid, "day", val] = (idxs, [1] * len(idxs))
                except ValueError:
                    "Do nothing"
                    
            if "year" in node.child:
                try:
                    val = node.child["year"][0]
                    year = str(int(val))
                    if len(year) == 2:
                        year = "20" + year
                    idxs = find_year(year, tokens)
                    if idxs:
                        alg[nodeid, "year", val] = (idxs, [1] * len(idxs))
                except ValueError:
                    "Do nothing"
            
            #Decade, century,...
            if "decade" in node.child:
                try:
                    val = node.child["decade"][0]
                    decade = str(int(val))
                    if len(decade) == 2:
                        decade = '19' + decade
                    idxs = find_decade(decade, tokens)
                    if idxs:
                        alg[nodeid, "decade", val] = (idxs, [1] * len(idxs))
                except ValueError:
                    "Do nothing"
                    
            if "time" in node.child:
                val = node.child["time"][0]
                time = val
                if time[0] == '\"':
                    time = time[1:-1]
                idxs = find_time(time, tokens)
                if idxs:
                    alg[nodeid, "time", val] = (idxs, [1] * len(idxs))
                    
            if "century" in node.child:
                try:
                    val = node.child["century"][0]            
                    cent = str(val)
                    if len(cent) >= 2:
                        cent = int(cent[:2])
                    else:
                        cent = int(cent)
                    idxs = find_cent(cent, tokens)
                    if idxs:
                        alg[nodeid, "century", val] = (idxs, [1] * len(idxs))
                except ValueError:
                    "Do nothing"
                    
            if "weekday" in node.child:
                val = node.child["weekday"][0]
                week_day = val
                idxs = find_weekday(week_day.inst, tokens)
                if idxs:
                    alg[nodeid, "weekday", val] = (idxs, [1] * len(idxs))
                    
            continue
        