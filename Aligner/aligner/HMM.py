# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 20:52:24 2016

@author: mrudul
"""

#Hidden Markov Model for probabilities conditioned on parent alignment
from .Objects import AMRNode, Alignment
import pickle



#Global vars
emthres = 0.5



#distance between two spans
def get_dist(span1, span2):
    start1, end1 = span1
    start2, end2 = span2
    if start2 >= end1:
        return start2 - end1 + 1
    elif start1 >= end2:
        return start1 - end2 + 1
    else:
        return 0

def get_prob(span1, span2, transprobs):
    if span1 is None:
        return transprobs[None,1]
    elif span2 is None:
        return transprobs[1,None]
        
    d = get_dist(span1, span2)
    return transprobs[span1][d]

#Compute transition probabilities from all spans
def get_trans(slen, counts, alg):
        transprobs = {}
        transprobs[1,None] = counts[slen,1,None]
        transprobs[None,1] = counts[slen,None,1]
        for x in range(0, slen):
            maxdist = max(x, slen-x-1)
            Z = sum(counts[a] for a in range(x+1))
            Z += sum(counts[a] for a in range(1,slen-x))
            Z += transprobs[1,None]
            entries = [0.0] * (maxdist+1)
            transprobs[x,x+1] = entries
            for z in range(0, maxdist+1):
                entries[z] = counts[z]/Z
        
        for nodeid,idxs_probs in alg.items():
            idxs = idxs_probs[0]
            for idx in idxs:
                if idx not in transprobs:
                    x,y = idx
                    maxdist = max(x, slen-y)
                    Z = sum(counts[a] for a in range(1,x+1))
                    Z += counts[0] * (y-x)
                    Z += sum(counts[a] for a in range(1,slen-y+1))
                    Z += transprobs[1,None]
                    entries = [0.0] * (maxdist+1)
                    transprobs[x,y] = entries
                    for z in range(0, maxdist+1):
                        entries[z] = counts[z]/Z
        
        return transprobs

#Viterbi algorithm - find most likely sequence of alignments
def viterbi(tokens, root, emprobs, transprobs, initalg):
    v = {}
    max_seq = {}
    n = len(tokens)
    probs = {}
    viterbi_r(tokens, root, emprobs, transprobs, initalg, v, max_seq, n, probs)
    start_prob = 1/(n+1)
    for idx in v[root.id]:
        v[root.id][idx] *= start_prob
        
    max_prob = 0.0
    max_idx = None
    for idx,p in v[root.id].items():
        if p > max_prob:
            max_prob = p
            max_idx = idx
    alg = {}
    alg[root.id] = max_idx
    viterbi_path(v, max_seq, root, max_idx, alg)
    
    return alg, probs


def prune(alg, thres):
    minprob = max(alg.values()) * thres
    keys = list(alg.keys())
    for key in keys:
        if alg[key] < minprob:
            del alg[key]


def viterbi_r(tokens, node, emprobs, transprobs, alg, v, max_seq, n, p):
    if type(node) is tuple:
        tmp = {}
        if node in alg:
            idxs,probs = alg[node]
            for idx,prob in zip(idxs,probs):
                tmp[idx] = prob
        link = node[1]
        val = node[2]
        for i in range(n):
            if (i, i+1) not in tmp:
                tmp[(i, i+1)] = emprobs[(link,val), tokens[i]]
        prune(tmp, emthres)
        tmp[None] = emprobs[(link,val), None]
        v[node] = tmp
        p[node] = tmp.copy()
        return
        
    tmp =  {}
    if node.id in alg:
        idxs,probs = alg[node.id]
        for idx,prob in zip(idxs,probs):
            tmp[idx] = prob
    for i in range(n):
        if (i, i+1) not in tmp:
            tmp[(i, i+1)] = emprobs[node.inst, tokens[i]]
    prune(tmp, emthres)
    tmp[None] = emprobs[node.inst, None]
    p[node.id] = tmp.copy()
    
    for key,val in node.child.items():
        if type(val) is AMRNode:
            viterbi_r(tokens, val, emprobs, transprobs, alg, v, max_seq, n, p)
            maxtmp = {}
            for idx1,p1 in tmp.items():
                max_p = 0.0
                max_idx = None
                childtmp = v[val.id]
                for idx2,p2 in childtmp.items():
                    prob = get_prob(idx1, idx2, transprobs)*p2
                    if prob > max_p:
                        max_p = prob
                        max_idx = idx2
                tmp[idx1] *= max_p
                maxtmp[idx1] = max_idx
            max_seq[val.id] = maxtmp
        else:
            node_tuple = (node.id, key, val)
            viterbi_r(tokens, node_tuple, emprobs, transprobs, alg, v, max_seq, n, p)
            maxtmp = {}
            for idx1,p1 in tmp.items():
                max_p = 0.0
                max_idx = None
                childtmp = v[node_tuple]
                for idx2,p2 in childtmp.items():
                    prob = get_prob(idx1, idx2, transprobs)*p2
                    if prob > max_p:
                        max_p = prob
                        max_idx = idx2
                tmp[idx1] *= max_p
                maxtmp[idx1] = max_idx
            max_seq[node_tuple] = maxtmp
    
    v[node.id] = tmp


def viterbi_path(v, max_seq, node, idx, alg):
    for key,val in node.child.items():
        if type(val) is AMRNode:
            max_idx = max_seq[val.id][idx]
            alg[val.id] = max_idx
            viterbi_path(v, max_seq, val, max_idx, alg)
        else:
            max_idx = max_seq[node.id,key,val][idx]
            alg[node.id, key, val] = max_idx


#Estimate alignment probabilities in viterbi path
def probabilities(root, alg, probs, transprobs, sntlen):
    p = {}
    probs_r(root, alg, probs, transprobs, p, 1/(sntlen+1))
    return p
    
def probs_r(node, alg, probs, transprobs, p, q):
    if type(node) is tuple:
        p[node] = q*probs[node][alg[node]]
    else:
        idx1 = alg[node.id]       
        p[node.id] = q*probs[node.id][idx1]
        for key,val in node.child.items():
            if type(val) is AMRNode:
                idx2 = alg[val.id]
                t = get_prob(idx1, idx2, transprobs)
                probs_r(val, alg, probs, transprobs, p, t)
            else:
                idx2 = alg[node.id, key, val]
                t = get_prob(idx1, idx2, transprobs)
                probs_r((node.id, key, val), alg, probs, transprobs, p, t)   



#Return most likely sequence of alignments
def most_likely(tokens, graph, emprobs, hmmcounts, alg):
    n = len(tokens)
    t = get_trans(n, hmmcounts, alg)
    alg,p = viterbi(tokens, graph.root, emprobs, t, alg)
    probs = probabilities(graph.root, alg, p, t, len(tokens))
    #return finalize(alg, probs, graph.ref)
    return Alignment(alg)

#One-One alignment
def finalize(alg, probs, nodes):
    alg = Alignment(alg)
    spans = alg.spans
    refs = alg.ref
    for span in spans:
        if span is None:
            continue
        nids = spans[span]
        if len(nids) > 1:
            maxprob = 0.0
            maxnid = None
            for nid in nids:
                p = probs[nid]
                if maxnid is None or p > maxprob:
                    maxnid = nid
                    maxprob = p
            maxnids = [maxnid]
            nids.remove(maxnid)
            has_neighbor = True
            while nids and has_neighbor:
                has_neighbor = False
                i = 0
                m = len(nids)
                n = len(maxnids)
                while i < m:
                    nid = nids[i]
                    for j in range(n):
                        if neighbors(nid, maxnids[j], nodes):
                            has_neighbor = True
                            maxnids.append(nid)
                            nids.remove(nid)
                            m -= 1
                            i -= 1
                            break
                    i += 1
            spans[span] = maxnids
            for key in nids:
                refs[key] = None
                
    return alg

def neighbors(nid1, nid2, nodes):
    if type(nid1) is tuple and type(nid2) is tuple:
        return nid1[0] == nid2[0]
    elif type(nid1) is tuple:
        return nid1[0] == nid2
    elif type(nid2) is tuple:
        return nid2[0] == nid1
    else:
        node2c = nodes[nid2].child.values()
        for c in node2c:
            if type(c) is AMRNode and c.id == nid1:
                return True
        node1c = nodes[nid1].child.values()
        for c in node1c:
            if type(c) is AMRNode and c.id == nid2:
                return True
        return False
    


#calculate expected counts
def update_counts(counts, alg, node, n):
    span1 = alg[node.id]
    for key,val in node.child.items():
        if type(val) is AMRNode:
            span2 = alg[val.id]
            update_counts(counts, alg, val, n)
        else:
            span2 = alg[node.id, key, val]
            
        counts[n,"total"] += 1.0
        if span1 is None:
            counts[n,None,1] += 1.0
        elif span2 is None:
            counts[n,1,None] += 1.0
        else:
            d = get_dist(span1, span2)
            counts[d] += 1.0
            



def train(sentences, graphs, emprobs, savefile="/tmp/probs.hmm", numiter=20, initalg=[], method="viterbi"):
    n = len(sentences)
    
    print("Initializing HMM model")
    #Initialize params
    maxlen = max(len(snt) for snt in sentences)
    p = 1/maxlen
    d = {}
    for k in range(0, maxlen):
        d[k] = p
        d[k,1,None] = p
        d[k,None,1] = p
    d[maxlen,1,None] = p
    d[maxlen,None,1] = p
    
    if not initalg:
        initalg = [{}] * n
    
    print("training")
    delta = 100.0   
    for i in range(numiter):
        if delta == 0.0:
            break
        #set counts
        counts = {}
        for k in range(0, maxlen):
            counts[k] = 0.0
            counts[k,1,None] = 0.0
            counts[k,None,1] = 0.0
            counts[k, "total"] = 0.0
        counts[maxlen,1,None] = 0.0
        counts[maxlen,None,1] = 0.0
        counts[maxlen,"total"] = 0.0
                         
        #Expectation
        for k in range(n):
            root = graphs[k].root
            alg = most_likely(sentences[k], graphs[k], emprobs, d, initalg[k])
            update_counts(counts, alg, root, len(sentences[k]))
        
        #Maximization
        delta = 0.0
        for j in range(maxlen):
            old = d[j]
            d[j] = counts[j]
            delta += abs(d[j] - old)
            if counts[j,"total"] > 0.0:
                old = d[j,1,None]
                d[j,1,None] = counts[j,1,None]/counts[j,"total"]
                delta += abs(d[j,1,None] - old)
                old = d[j,None,1]
                d[j,None,1] = counts[j,None,1]/counts[j,"total"]
                delta += abs(d[j,None,1] - old)
        if counts[maxlen,"total"] > 0.0:
            old = d[maxlen,1,None]
            d[maxlen,1,None] = counts[maxlen,1,None]/counts[maxlen,"total"]
            delta += abs(d[maxlen,1,None] - old)
            old = d[maxlen,None,1]
            d[maxlen,None,1] = counts[maxlen,None,1]/counts[maxlen,"total"]
            delta += abs(d[maxlen,None,1] - old)
        
        print("Iteration " + str(i+1) +". delta=" + str(delta))
        pickle.dump(d, open(savefile, "wb"))
    
    return d

def load_model(loadfile="/tmp/probs.hmm"):
    return pickle.load(open(loadfile, "rb"))