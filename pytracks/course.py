#!/usr/bin/python -u 

import string, sys

class Course:
    def __init__(self, id, elevChange, dist, descrptn):
        self.id = id
        self.elevChange = elevChange
        self.dist = dist
        self.descrptn = descrptn
        if self.elevChange == 0: print>>sys.stderr, "WARNING: no elev for course", self.id
        if self.dist == 0: print>>sys.stderr, "WARNING: no distance for course", self.id
        if self.descrptn == 0: print>>sys.stderr, "WARNING: no description for course", self.id

    @classmethod
    def fromString(cls, line):
        numFields = 3
        tokens = string.split(line, None, numFields)
        return cls(id = tokens[0], elevChange = float(tokens[1]), 
                   dist = float(tokens[2]), 
                   descrptn = tokens[3].rstrip())
    
    def write(self, outFile):
        print >> outFile, "%-10s" % self.id,\
            "%8.0f" % self.elevChange,\
            "%6.2f" % self.dist,\
            " " + self.descrptn
