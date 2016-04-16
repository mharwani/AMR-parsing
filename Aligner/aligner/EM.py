# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 01:54:23 2016

@author: mrudul
"""

#Expectation-Maximization
#Generating transaltional lexicon probabilities with EM
import pickle
from .Objects import AMRNode



def train(sentences, graphs, savefile="/tmp/probs.em", numiter=20):
    n = len(sentences)
    
    print("Initializing EM model")
    #Initialize counts and probs
    count = {}
    prob = {}
    for k in range(n):
        for token in sentences[k] + [None]:
            count[token] = 0.0
            nodes = graphs[k].ref
            for nodeid in nodes:
                node = nodes[nodeid]
                count[node.inst, token] = 0.0
                prob[node.inst, token] = 1.0
                for key,val in node.child.items():
                    if type(val) is not AMRNode:
                        count[(key, val), token] = 0.0
                        prob[(key, val), token] = 1.0
    total = len(prob)
    for key in prob:
        prob[key] = float(1/total)
        
    print("training")
    #EM
    for i in range(numiter):
        #Reset counts
        for key in count:
            count[key] = 0.0
        #E-step
        for k in range(n):
            for token in sentences[k] + [None]:
                nodes = graphs[k].ref
                Z = 0.0 #normalization term
                for nodeid, node in nodes.items():
                    Z += prob[node.inst, token]
                    for key,val in node.child.items():
                        if type(val) is not AMRNode:
                            Z += prob[(key, val), token]
                for nodeid, node in nodes.items():
                    c = prob[node.inst, token]/Z
                    count[node.inst, token] += c
                    count[token] += c
                    for key,val in node.child.items():
                        if type(val) is not AMRNode:
                            c = prob[(key, val), token]/Z
                            count[(key, val), token] += c
                            count[token] += c
        #M-step
        a = 0.0
        for key,token in prob:
            p = count[key, token]/count[token]
            a += abs(prob[key,token] - p)
            prob[key,token] = p
        
        pickle.dump(prob, open(savefile, "wb"))
        print("Iteration " + str(i+1) + "/" + str(numiter) + ". delta=" + str(a))
    
    return prob


def load_model(loadfile="/tmp/probs.em"):
    return pickle.load(open(loadfile, "rb"))