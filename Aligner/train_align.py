# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 03:32:31 2016

@author: mrudul
"""

#Train models and align amr files

#USAGE: train_align.py -f file1 file2... -em num_iterations_em -hmm num_iterations_hmm
from aligner import Aligner, EM, HMM
from aligner.Objects import AMRGraph
import sys
import os
from train import train_models
from align import align_file



if __name__ == "__main__":
    #Load parameters
    args = sys.argv
    i = 1
    n = len(args)
    fnames = []
    emiter = 40
    hmmiter = 40
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
        else:
            print("Invalid argument: " + args[i])
            sys.exit("USAGE: train_align.py -f <AMR files> -em <number of iterations> -hmm <number of iterations>")
    
    #Train
    print("---TRAINING---")
    train_models(fnames, emiter, hmmiter, "model")
    em = EM.load_model("model.em")
    hmm = HMM.load_model("model.hmm")
    
    #Align
    print("\n\n---ALIGNING---")
    for fname in fnames:
        base = os.path.basename(fname)
        print(base)
        n = len(base)
        while n > 0:
            n -= 1
            if base[n] == '.':
                break
        foutname = base[:n] + ".alignment"
        fin = open(fname, "r")
        fout = open(foutname, "w")
        align_file(fin, fout, em, hmm)
    
    print("---DONE---")