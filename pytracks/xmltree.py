import sys
from lxml import etree

class XMLTree:
    def __init__(self, fname, namespace, root):
        self.ns = namespace
        self.tree = etree.parse(fname)
        self.root = root
        
    def findAll(self, token, isFloat = True):
        if isFloat: 
            return [float(t.text) for t in self.tree.xpath(self.root + token, namespaces=self.ns)]
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

    def addElem(self, parent, child, value):
        elem = etree.Element("{" + self.ns.values()[0] + "}" + child)
        elem.text = str(value)
        t = self.tree.xpath(self.root + parent, namespaces = self.ns)[0]
        t.append(elem)

    def delElem(self, parent, child):
        t = self.tree.xpath(self.root + parent, namespaces = self.ns)[0]
        for c in t:
            if c.tag == "{" + self.ns.values()[0] + "}" + child:
                t.remove(c)
                break

    def write(self, outf):
        self.indent(self.tree.getroot())
        self.tree.write(outf)

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for e in elem:
                self.indent(e, level+1)
                if not e.tail or not e.tail.strip():
                    e.tail = i + "  "
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
