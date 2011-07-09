from lxml import etree

class XMLTree:
    def __init__(self, fname, namespace, root):
        self.ns = namespace
        try:
            self.tree = etree.parse(fname)
        except etree.XMLSyntaxError as e:
            print "Cannot parse XML for", fname
            self.tree = None
        self.root = root
        
    def find_all(self, token, is_float=True):
        if self.tree is None: return [None]
        if is_float: 
            return [float(t.text) for t in self.tree.xpath(self.root + token, namespaces=self.ns)]
        else: return [t.text for t in self.tree.xpath(self.root + token, namespaces=self.ns)]
    
    def add_elems(self, parent, child, values, must_exist):
        i = 0
        for t in self.tree.xpath(self.root + parent, namespaces = self.ns):
            if must_exist != None:
                if t.find("{" + self.ns.values()[0] + "}" + must_exist) is None: continue
            elem = etree.Element("{" + self.ns.values()[0] + "}" + child)
            elem.text = str(values[i])
            t.append(elem)
            i += 1
            if i >= len(values): break

    def add_elem(self, parent, child, value):
        elem = etree.Element("{" + self.ns.values()[0] + "}" + child)
        elem.text = str(value)
        t = self.tree.xpath(self.root + parent, namespaces = self.ns)[0]
        t.append(elem)

    def del_elem(self, parent, child):
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
