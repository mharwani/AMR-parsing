# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 08:42:35 2016

@author: mrudul
"""

import re



#Word values
units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]
      
units_ordinal = [
        "", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
        "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth",
        "sixteenth", "seventeenth", "eighteenth", "nineteenth"
      ]
uord = {}
for idx, word in enumerate(units_ordinal):
    uord[word] = idx
      
tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

scales = ["hundred", "thousand", "million", "billion", "trillion"]

numwords = {}
numwords["and"] = (1, 0)
numwords["a"] = (1, 0)
numwords["of"] = (1, 0)

for idx, word in enumerate(units):    
    numwords[word] = (1, idx)
    if word != "six":
        numwords[word + "s"] = (1, idx)
    else:
        numwords["sixes"] = (1, 6)
        
for idx, word in enumerate(tens):     
    numwords[word] = (1, idx * 10)
    numwords[word[:-1] + "ies"] = (1, idx * 10)
    numwords[word[:-1] + "ieth"] = (1, idx * 10)
    
for idx, word in enumerate(scales):   
    numwords[word] = (10 ** (idx * 3 or 2), 0)
    numwords[word + "s"] = (10 ** (idx * 3 or 2), 0)

numwords["dozen"] = (12, 0)
numwords["dozens"] = (12, 0)

numwords["couple"] = (2, 0)
numwords["couples"] = (2, 0)

del units
del units_ordinal
del tens


#Convert words to numbers
def getnum(tokens):
    numbers = []
    indxs = []
    n = len(tokens)
    i = 0
    while i < n:
        fl = None
        while i < n and tokens[i] not in numwords:
            #digits
            parts = tokens[i].split(',')
            if all([part.isdigit() for part in parts]):
                s = ''.join(parts)
                fl = float(s)
                break
            #Ordinals
            elif tokens[i] in uord:
                numbers.append(float(uord[tokens[i]]))
                indxs.append((i, i+1))
                i += 1
                continue
            elif tokens[i][-2:] in ("st", "th", "nd", "rd") and tokens[i][:-2].isdigit():
                numbers.append(float(tokens[i][:-2]))
                indxs.append((i, i+1))
                i += 1
                continue
            #Extract floats from alphanumeric tokens
            nums = re.findall(r'\d+(?:\.\d+)?', tokens[i])
            if nums:
                if len(nums) == 1:
                    fl = float(nums[0])
                    break
                else:
                    for num in nums:
                        numbers.append(float(num))
                        indxs.append((i, i+1))
            i += 1
                
        if i == n:
            break
        elif tokens[i] in ("and", "of"):
            i += 1
            continue
        
        start = i
        current = result = 0.0
        if fl is not None:
            if i < n-1 and tokens[i+1] in scales:
                current = fl
                i += 1
            else:
                numbers.append(fl)
                indxs.append((i, i+1))
                i += 1
                continue
        while i < n:
            if tokens[i] in numwords:
                scale, increment = numwords[tokens[i]]
                current = (current * scale + increment)
                if scale > 1 and scale != 100:
                    if current != 0.0:
                        result += current
                        current = 0.0
                    else:
                        result += float(scale)
                elif scale == 100 and current == 0.0:
                    current = 100.0
                
            elif tokens[i] == ",":
                i += 1
                continue
            else:
                break

            i += 1
        
        if tokens[i-1] in ["and", ",", "a", "of"]:
            end = i-1
        else:
            end = i
        if end > start:
            numbers.append(result+current)
            indxs.append((start, end))

    return (numbers, indxs)


#Search numeric quantities. Returns spans of token indexes
def search_num(value, numbers, indexes):
    n = len(numbers)
    idxs = []
    for i in range(n):
        if value == numbers[i]:
            idxs.append(indexes[i])
    return idxs