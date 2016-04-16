# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 18:36:18 2016

@author: mrudul
"""


#Train Expectation-Maximization and Hidden Markov Model

#USAGE: train.py -f file1 file2 ... -em number_of_iterations_for_em -hmm number_of_iterations_for_hmm -model model_name
from aligner import Aligner, EM, HMM
from aligner.Objects import AMRGraph
import sys



def train_models(fnames, emiter, hmmiter, model_name):
    if not fnames:
        sys.exit("No file provided")

    print("Reading AMR files")
    pairs = []
    for fname in fnames:
        f = open(fname, "r")
        pairs += Aligner.readAMR(f)
        f.close()
    sentences = [Aligner.tokenize(pair[0]) for pair in pairs]
    graphs = [AMRGraph(pair[1], False) for pair in pairs]

    emprobs = EM.train(sentences, graphs, model_name + ".em", emiter)
    #emprobs = EM.load_model(model_name + ".em")
    print("Initializing rule-based alignments")
    n = len(sentences)
    initalgs = [{}] * n
    for i in range(n):
        initalgs[i] = Aligner.initalign(graphs[i].ref, sentences[i])
        if (i+1) % 1000 == 0:
            print(str(i+1) + "/" + str(n))
    hmmprobs = HMM.train(sentences, graphs, emprobs, model_name + ".hmm", hmmiter, initalgs)
    print("Done")
    
    
if __name__ == "__main__":  
    #Load parameters and execute
    args = sys.argv
    i = 1
    n = len(args)
    fnames = []
    emiter = 40
    hmmiter = 40
    model_name = "model"
    while i < n:
        if args[i] == "-f":
            i += 1
            while i < n and args[i][0] != '-':
                fnames.append(args[i])
                i += 1
        elif args[i] == "-em":
            emiter = int(args[i+1])
            i += 2
        elif args[i] == "-hmm":
            hmmiter = int(args[i+1])
            i += 2
        elif args[i] == "-model":
            model_name = args[i+1]
            i += 2
        else:
            print("Invalid argument: " + args[i])
            sys.exit("USAGE: train.py -f <AMR files> -em <number of iterations> -hmm <number of iterations> -model <model name>")
    
    train_models(fnames, emiter, hmmiter, "model")