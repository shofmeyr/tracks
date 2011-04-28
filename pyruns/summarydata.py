#!/usr/bin/python -u 

import sys

from run import Run, getTimeFromFname

class SummaryData:
    def __init__(self):
        self.runs = []
        self.comments = {}
        
    def load(self, fname):
        self.runs = []
        self.comments = {}
        f = open(fname, "rw+")
        i = 0
        for line in f.readlines():
            if line.strip() == "": continue
            if line.lstrip()[0] == "#": 
                # multiline comments
                if not i in self.comments: self.comments[i] = ""
                self.comments[i] += line.lstrip()
            else: 
                self.runs.append(Run.fromString(line))
                i += 1
        f.close()
        print "Loaded data from", self.runs[0].startTime, "to", self.runs[-1].startTime

    def save(self, outFile):
        i = 0
        for run in self.runs:
            if i in self.comments: print >> outFile, self.comments[i],
            run.write(outFile)
            i += 1
        if i in self.comments: print>>outFile, self.comments[i],
        print "Saved data from", self.runs[0].startTime, "to", self.runs[-1].startTime
            
    def updateFromXML(self, fnames):
        totTime = 0.0
        totDist = 0.0
        if len(self.runs) > 0: mostRecentTime = self.runs[-1].startTime
        else: mostRecentTime = dt.strptime("1970-01-01", "%Y-%m-%d")
        print "Updating... ",
        sys.stdout.flush()
        firstRun = True
        for fname in fnames: 
            if getTimeFromFname(fname) <= mostRecentTime: continue
            if firstRun:
                firstRun = False
                print "found runs:\n",\
                    "#        start time  dist rdist   time  mxPc  avPc  mxHR  avHR  elev eRate   eff  crs"
            run = Run.fromXMLFile(fname)
            if run == None: continue
            self.runs.append(run)
            run.write(sys.stdout)
            totDist += run.dist
            totTime += run.duration
        if not firstRun: print "Updated %.2f miles, %.1f mins" % (totDist, totTime)
        else: print "no runs added"
        return not firstRun
    
    def getEfficiencies(self):
        effs = []
        for run in self.runs: effs.append(run.efficiency)
        return effs

    def getElevRates(self):
        elevRates = []
        for run in self.runs: elevRates.append(run.elevRate)
        return elevRates
    


