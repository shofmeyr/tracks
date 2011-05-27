import sys
from lxml import etree

class XMLTree:
    def __init__(self, fname, namespace, root):
        self.ns = namespace
        self.tree = etree.parse(fname)
        self.root = root
        
    def findAll(self, token, isFloat = True):
        if isFloat: return [float(t.text) for t in self.tree.xpath(self.root + "t:" + token, namespaces=self.ns)]
        else: return [t.text for t in self.tree.xpath(self.root + "t:" + token, namespaces=self.ns)]
    
