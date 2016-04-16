#Aligner functions

from nltk.tokenize import word_tokenize

from .Objects import AMRNode, AMRGraph
from . import words2num, wordmatch, entitymatch, HMM

import re
import csv
import sys



#Tokenizer regex pattern
tokPattern = r"[a-zA-Z_\d]+|(?:\'s)|[^\s\da-zA-Z_]+"


#Read AMR file
def readAMR(afile):
    pairs = []
    snt = ''
    amr = ''
    i = 0
    
    for line in afile:
        i += 1
        if not line.strip():
            if amr:
                pairs.append((snt, amr))
                snt = ''
                amr = ''
        elif '::snt ' in line:
            if snt:
                raise Exception("in line " + str(i) + ".", "Expecting: AMR. Got: snt")
            else:
                ind = line.find('::snt ') + 6
                snt = line[ind:]
        elif '#' not in line:
            if snt:
                amr += line
            else:
                raise Exception("in line " + str(i) + ".", "Expecting: snt. Got: AMR")
    if snt and amr:
        pairs.append((snt, amr))

    return pairs
    

#Tokenize a sentence
def tokenize(snt):
    _words = word_tokenize(snt)
    snt_tokens = []
    for word in _words:
        if len(word) > 1 and word[0] == "\'":
            if len(word) > 2 or word[1] != 's':
                snt_tokens.append("\'")
                word = word[1:]
        tokens = re.split(r'([-]+|[\*]+)', word)
        for token in tokens:
            if token:
                snt_tokens.append(token)
    return [token.lower() for token in snt_tokens]


#Initialize alignment
def initalign(nodes, tokens):
    alg = {}
    
    #First pass - Entity matching (countries, dates, etc,)
    entitymatch.align(nodes, tokens, alg)  
    
    #Second pass - Word matching
    #Preprocessing
    nums,numidxs = words2num.getnum(tokens)
    lemmas = wordmatch.getlemmas(tokens)
    
    for nodeid, node in nodes.items():
        if nodeid in alg:
            continue
        
        #Literals and quantities        
        for key, val in node.child.items():
            if type(val) is AMRNode:
                continue
            elif (nodeid, key, val) in alg:
                continue
            
            #Align quantities
            if type(val) is float:
                idxs = words2num.search_num(val, nums, numidxs)
                if idxs:
                    alg[nodeid, key, val] = (idxs, [1] * len(idxs))
                
            #Align Literals
            elif type(val) is str and val[0] == "\"":
                lit = val[1:-1]
                idxs,probs = wordmatch.search_subseq(lit, tokens)
                if idxs:
                    alg[nodeid, key, val] = (idxs, probs)
                
        #Align Instance name
        words = node.inst.split('-')
        n = len(words)
        #Remove frameset id
        if n > 1 and words[-1].isdigit():
            words.pop()
            n -= 1
                    
        #Multiple token alignment - longest subsequence
        if n > 1:
            idxs, probs = wordmatch.search_subseq("".join(words), tokens)
            if idxs:
                alg[nodeid] = (idxs, probs)
                
        #Single token alignment - wordnet
        else:
            idxs, probs = wordmatch.search_wordnet(words[0], lemmas)
            if idxs:
                alg[nodeid] = (idxs, probs)
    
    
    return alg
    
    
#Align
def align(snt, amr, em, hmm):
    graph = AMRGraph(amr, False)
    tokens = tokenize(snt)
    nodes = graph.ref
    
    #Initialize alignment    
    alg = initalign(nodes, tokens)
    
    #Most likely alignment sequence
    alg = HMM.most_likely(tokens, graph, em, hmm, alg)
    
    return alg, nodes, tokens           
              

def alignPairs(pairs, em, hmm):
    i = 0
    n = len(pairs)
    a = []
    for i in range(n):
        snt,amr = pairs[i]
        a.append(align(snt,amr, em, hmm))
        i += 1
        if i % 100 == 0:
            print(str(i) + "/" + str(n))
    return a


def printAlignments(algs, pairs, afile):
    n = len(pairs)
    for i in range(n):
        alg, nodes, tokens = algs[i]
        snt,amr = pairs[i]
        spans = list(alg.spans.keys())
        span_ref = alg.spans
        None_flag = True
        try:
            spans.remove(None)
        except ValueError:
            None_flag = False
        spans = sorted(spans, key=lambda s: s[1])
        if None_flag:
            spans.append(None)
        afile.write("# ::snt " + snt + "\n")
        afile.write(amr + "\n")
        afile.write("# ::alignments\n")
        for span in spans:
            if span is None:
                afile.write("# ::NULL ")
            else:
                start,end = span
                afile.write("# " + " ".join(tokens[start:end]) + " ")
            nodeids = span_ref[span]
            groups = []
            for nid in nodeids:
                if type(nid) is tuple:
                    nid0 = nid[0]
                    if nid0 not in nodeids and nid0 not in groups:
                        groups.append(nid0)
                elif nodes[nid].parent not in nodeids:
                    groups.append(nid)
            string = " ".join([DFS_print(nid, nodes, nodeids) for nid in groups])
            afile.write(string + "\n")
        afile.write("\n\n\n")


def DFS_print(nid, nodes, nodeids):
    node = nodes[nid]
    children = ""
    for key,val in node.child.items():
        if type(val) is not AMRNode:
            if (nid,key,val) in nodeids:
                children += " :" + key + " " + str(val)
    for key,val in node.child.items():
        if type(val) is AMRNode:
            if val.id in nodeids:
                children += " :" + key + " " + DFS_print(val.id, nodes, nodeids)
    if nid in nodeids:
        return "(" + nid + " / " + node.inst + children + ")"
    else:
        return "(" + nid + children + ")"
    

def findPairs(pairs, string):
    i = 0
    n = len(pairs)
    idxs = []
    for i in range(n):
        if string in pairs[i][0]:
            print("Found i = " + str(i))
            print(pairs[i][0])
            idxs.append(i)
    return idxs