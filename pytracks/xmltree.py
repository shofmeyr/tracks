import sys
from lxml import etree

class XMLTree:
    def __init__(self, fname, namespace, root):
        self.ns = namespace
        self.tree = etree.parse(fname)
        self.root = root
        
    def findAll(self, token, isFloat = True):
        if isFloat: return [float(t.text) for t in self.tree.xpath(self.root + token, namespaces=self.ns)]
        else: return [t.text for t in self.tree.xpath(self.root + token, namespaces=self.ns)]
    
    def addElems(self, parent, child, values, mustExist):
        i = 0
        for t in self.tree.xpath(self.root + parent, namespaces = self.ns):
            if mustExist != None:
                if t.find("{" + self.ns.values()[0] + "}" + mustExist) == None: continue
            elem = etree.Element("{" + self.ns.values()[0] + "}" + child)
            elem.text = str(values[i])
            t.append(elem)
            i += 1
            if i >= len(values): break

    def write(self, outf):
        self.tree.write(outf)
