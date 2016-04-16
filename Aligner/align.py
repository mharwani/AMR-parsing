# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 17:54:23 2016

@author: mrudul
"""

#Align AMR file using model.em and model.hmm

#USAGE: align.py AMR_input_file output_file -model model_name

from aligner import Aligner, EM, HMM
import sys



def align_file(fin, fout, em_model, hmm_model):
    pairs = Aligner.readAMR(fin)
    print("Aligning")
    algs = Aligner.alignPairs(pairs, em_model, hmm_model)
    print("Writing alignments to file")
    Aligner.printAlignments(algs, pairs, fout)
    print("done")


if __name__ == "__main__":   
    #load parameters
    try:       
        fin = open(sys.argv[1], "r")
        fout = open(sys.argv[2], "w")
    except IndexError:
        System.exit("USAGE: align.py <AMR input file> <output file> -model <model name>")
    model_name = "model"

    args = sys.argv[3:]
    i = 0
    n = len(args)
    while i < n:
        if args[i] == "-model":
            model_name = args[i+1]
            i += 2
        else:
            print("Invalid argument: " + args[i])
            System.exit("USAGE: align.py <AMR input file> <output file> -model <model name>")

    #load models
    em = EM.load_model(model_name + ".em")
    hmm = HMM.load_model(model_name + ".hmm")
    
    align_file(fin, fout, em, hmm)
    fin.close()
    fout.close()
