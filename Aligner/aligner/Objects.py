#Class definitions for alignment

import re
from collections import OrderedDict

#AMR Node
class AMRNode:
    def __init__(self, instance, identity):
        self.inst = instance
        self.id = identity
        self.child = DupDict()
        self.parent = None
        self.numchild = 0
        self.polarity = False
        
    def set_inst(self, instance):
        self.inst = instance
        
    def set_id(self, identity):
        self.id = identity
    
    def add_child(self, link, child):
        self.child[link] = child
        self.numchild += 1
    
    def remove_child(self, link):
        del self.child[link]
        self.numchild -= 1
    
    def add_literal(self, link, value):
        self.child[link] = value
    
    def add_numeric(self, link, value):
        self.child[link] = value
        
    def add_constant(self, link, value):
        self.child[link] = value
    
    def negate(self):
        self.polarity = True
        

#AMR Graph
class AMRGraph:
    @staticmethod       
    def parse_node(node, tokens, i, ref):
        i += 1
        node_id = tokens[i]
        if node_id in ref:
            k = 0
            if node_id[-1].isdigit():
                newid = node_id[:-1] + str(k)
            else:
                newid = node_id + str(k)
            while newid in ref:
                k += 1
                newid[-1] = str(k)
            node_id = newid
        node.set_id(node_id)
        ref[node_id] = node
        i += 1
        if tokens[i] == '/':
            node.set_inst(tokens[i+1])
            i += 2
        
        #add children
        while tokens[i] != ')':
            if tokens[i] == ':':
                link = tokens[i+1]
                i += 2
                
                #Numeric
                fl = None
                try:
                    fl = float(tokens[i])
                except ValueError:
                    "Do nothing"
                if fl:
                    node.add_numeric(link, fl)
                #Literal
                elif tokens[i][0] == '\"':
                    node.add_literal(link, tokens[i])
                #new node
                elif tokens[i] == '(':
                    new_node = AMRNode(None, None)
                    new_node.parent = node.id
                    node.add_child(link, new_node)
                    i = AMRGraph.parse_node(new_node, tokens, i, ref)
                #Reference or a constant
                else:
                    node.add_constant(link, tokens[i])
            
            i += 1
        
        return i
    
    @staticmethod
    def resolve_ref(ref):
        for node in ref.values():
            for key,val in node.child.items():
                if type(val) is str and val in ref:
                    node.add_child(key, ref[val])
    
    def parse(self, string, cross):
        tokens = re.findall(r'(\(|\)|\"[^\"]+\"|:|/|[^\s\(\):/\"]+)', string)
        if tokens[0] != '(':
            print('No root')
            return      
        self.root = AMRNode(None, None)
        AMRGraph.parse_node(self.root, tokens, 0, self.ref)
        #Resolve references
        if cross:
            AMRGraph.resolve_ref(self.ref)
        else:
            for node in self.ref.values():
                for key,val in node.child.items():
                    if type(val) is str and val in self.ref:
                        del node.child[(key,val)]
    
    def __init__(self, string, cross=True):
        self.nodes = {}
        self.root = None
        self.ref = OrderedDict()
        self.parse(string, cross)
        
    def print(self):
        AMRGraph.print_node(self.root, '', [])
        
    @staticmethod 
    def print_node(node, i, printed):
        printed.append(node.id)
        print(i + '(' + node.id + ' / ' + node.inst)
        i += '  '
        for link in node.numerics.keys():
            print(i + ':' + link + ' ' + str(node.numerics[link]))
        for link in node.literals.keys():
            print(i + ':' + link + ' ' + '\"' + node.literals[link] + '\"')
        for link in node.constants.keys():
            print(i + ':' + link + ' ' + node.constants[link])
        for link in node.child.keys():
            if node.child[link].id in printed:
                print(i + ':' + link + ' ' + node.child[link].id)
            else:
                print(i + ':' + link)
                AMRGraph.print_node(node.child[link], i, printed)
        print(i[0:len(i)-1] + ')')
        

#Alignment        
class Alignment:
    def __init__(self, alg):
        self.spans = {}
        self.ref = alg
        
        for nodeid, idx in alg.items():
            if idx in self.spans:
                self.spans[idx].append(nodeid)
            else:
                self.spans[idx] = [nodeid]
    
    def __getitem__(self, index):
        if type(index) is str:
            return self.ref[index]
        elif type(index) is tuple and type(index[0]) is str:
            return self.ref[index]
        else:
            return self.spans[index]
    
    def __setitem__(self, key, value):
        old_span = self.ref[key]
        self.spans[old_span].remove(key)
        self.ref[key] = value
        self.spans[value].append(key)
    
    def __contains__(self, item):
        if type(item) is str:
            return item in self.ref
        elif type(item) is tuple and type(item[0]) is str:
            return item in self.ref
        else:
            return item in self.spans
    
    @staticmethod
    def dist(span1, span2, tokens):
        d = 1
        i = span1[1]
        j = span2[0]
        while i < j:
            tok = tokens[i]
            if tok in ['.', ',', ';', '!', '?']:
                d += 3
            elif len(tok) > 2 and tok != 'the':
                d += 1
            i += 1
        return d
    
    @staticmethod
    def distances(tokens):
        n = len(tokens)
        dist = [0] * n
        for i in range(1,n):
            tok = tokens[i]
            if tok in ['.', ',', ';', '!', '?']:
                dist[i] = dist[i-1] + 3
            elif len(tok) > 2 and tok != 'the':
                dist[i] = dist[i-1] + 1
            else:
                dist[i] = dist[i-1]
        
        return dist


#Dictionary for duplicate keys
class DupDict:
    def __init__(self):
        self.hash = {}
    
    def __getitem__(self, key):
        return self.hash[key]
    
    def __setitem__(self, key, value):
        if key in self.hash:
            self.hash[key].append(value)
        else:
            self.hash[key] = [value]
    
    def __delitem__(self, item):
        if type(item) is tuple:
            key,val = item
            l = self.hash[key]
            l.remove(val)
            if not l:
                del self.hash[key]
        else:
            del self.hash[index]
    
    def __contains__(self, key):
        return key in self.hash
    
    def __iter__(self):
        return self.hash.keys()
    
    def items(self):
        ditems = self.hash.items()
        tuples = []
        for key,values in ditems:
            for value in values:
                tuples.append((key, value))
        return tuples
    
    def values(self):
        return sum(self.hash.values(), [])