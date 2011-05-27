import sys
from lxml import etree

class XMLTree:
    def __init__(self, fname):
        self.ns = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
        self.tree = etree.parse(fname)
        self.root = "t:Activities/t:Activity/t:Lap/"
        
    def findAll(self, token, isFloat = True):
        if isFloat: return [float(t.text) for t in self.tree.xpath(self.root + "t:" + token, namespaces={"t":self.ns})]
        else: return [t.text for t in self.tree.xpath(self.root + "t:" + token, namespaces={"t":self.ns})]
    
