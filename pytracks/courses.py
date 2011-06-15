#!/usr/bin/python -u 

import sys, string

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

class Courses:
    data = {}

    @classmethod
    def load(cls, fname):
        if fname == "": return
        try:
            f = open(fname, "r")
        except Exception as e:
            print>>sys.stderr, "Cannot open courses file \"" + fname + "\": " + str(e)
            return
            
        for line in f.readlines():
            if line.strip() == "": continue
            if line.lstrip()[0] == "#": continue
            course = Course.fromString(line)
            if course.id in Courses.data:
                print>>sys.stderr, "Duplicate course", course.id, "skipping..."
                continue
            Courses.data[course.id] = course
        f.close()
        if len(Courses.data) == 0: print>>sys.stderr, "Found no courses in \"" + fname + "\""
        else: print>>sys.stderr, "Loaded", len(Courses.data), "courses from \"" + fname + "\""

    

