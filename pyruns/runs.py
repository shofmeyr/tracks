#!/usr/bin/python -u 

import sys, pickle, os

from run import Run
from courses import Courses
from datetime import datetime as dt

class Runs:
    def __init__(self):
        self.runs = {}

    def load(self, fname):
        f = None
        if os.path.exists(fname + ".pck"): f = open(fname + ".pck", "r")
        if f != None:
            self.runs = pickle.load(f)
            f.close()
        if len(self.runs) == 0: print "Found no saved runs"
        else: print "Loaded data from", self.getSortedRuns()[0].startTime, "to", self.getSortedRuns()[-1].startTime
        
        return
        # below is my crued hack to input course and comments from a text file. Will be removed when other 
        # editing functionality is added
        f = open("summary.dat", "r")
        found = None
        for line in f.readlines():
            if line.strip() == "": continue
            if line.lstrip()[0] == "#": 
                if found != None: found.comment += "\n" + line.rstrip()
                continue
            savedRun = Run.fromString(line)
            found = None
            for run in self.runs.values():
                if savedRun.startTime == run.startTime: 
                    print "found run", savedRun.startTime, "in the file"
                    run.course = savedRun.course
                    run.comment = savedRun.comment
                    found = run
                    break
            if found == None: self.runs[savedRun.getStartTimeAsStr()] = savedRun
        f.close()

    def save(self, fname):
        f = open(fname + ".pck", "w+")
        pickle.dump(self.runs, f)
        f.close()
        print "Saved data from", self.getSortedRuns()[0].startTime, "to", self.getSortedRuns()[-1].startTime

    def updateFromXML(self, fnames):
        totTime = 0.0
        totDist = 0.0
        print "Updating... "
        skipAll = False
        for fname in fnames: 
            runId = os.path.basename(fname)
            update = False
            if runId in self.runs:
                if skipAll: continue
                print "Found run", runId, "corresponding to:"
                self.runs[runId].write(sys.stdout, "all")
                answer = raw_input("Would you like to update? (y)es/(N)o/(s)kip all ")
                if answer == "": continue
                if answer.lower() == "n": continue
                if answer.lower() == "s": skipAll = True
                else: update = True
            run = Run.fromXMLFile(fname)
            if run == None: continue
            totDist += run.dist
            totTime += run.duration
            if update: self.runs[runId].update(run)
            else: self.runs[runId] = run
        if totTime > 0: print "Updated %.2f miles, %.1f mins" % (totDist, totTime)
        else: print "no runs added"

    def getSortedRuns(self):
        return sorted(self.runs.values(), key=lambda run: run.startTime)

    def getEfficiencies(self):
        effs = []
        for run in self.getSortedRuns(): effs.append(run.efficiency)
        return effs

    def getElevRates(self):
        elevRates = []
        for run in self.getSortedRuns(): elevRates.append(run.elevRate)
        return elevRates
    
    def write(self, outFile, name = "all", useGps = False):
        Run.writeHeader(outFile)
        for run in self.getSortedRuns(): 
            if name == "all" or name == run.getStartTimeAsStr() or name == run.course:
                run.write(outFile, useGps)



