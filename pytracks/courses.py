#!/usr/bin/python -u 

import sys

from course import Course

class Courses:
    data = {}

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
    load = classmethod(load)

    

