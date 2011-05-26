import xml.etree.ElementTree as ElementTree

class XMLTree:
    def __init__(self, fname):
        # clean up xml file
        f = open(fname, "r+")
        cleanXml = ""
        addLine = False
        for line in f.readlines():
            if "Activities" in line: addLine = True
            if addLine: cleanXml += line.replace("xsi:", "")
            if "/Activities" in line: break
        f.close()
        self.tree = ElementTree.fromstring(cleanXml)
        
    def findAll(self, token):
        root = "Activity/Lap/"
        return [float(t.text) for t in self.tree.findall(root + token)]
    
