#!/usr/bin/python -u 

import sys, pickle, os
from track import Track

class Tracks:
    def __init__(self):
        self.data = {}
        self.index = 0
        self.sortedKeys = []

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def load(self, fname):
        # all the tracks are saved in one pickle file
        f = None
        if os.path.exists(fname): f = open(fname, "r")
        if f != None:
            try: 
                self.data = pickle.load(f)
                f.close()
            except Exception as e: "Could not load pickle file " + fname + ": " + str(e)
        self.sortedKeys = sorted(self.data.keys())
        if fname != "" and len(self.data) == 0: 
            print>>sys.stderr, "Found no saved tracks in \"" + fname + "\""
        else: print>>sys.stderr, "Loaded", len(self.data), "tracks from \"" + fname + "\":",\
                self.sortedKeys[0], "to", self.sortedKeys[-1]

    def save(self, fname):
        if fname == "": return
        try:
            f = open(fname, "w+")
            pickle.dump(self.data, f)
            f.close()
        except Exception as e:
            print>>sys.stderr, "Could not save data in " + fname + ": " + str(e)
            return
        print>>sys.stderr, "Saved data for", len(self.data), \
            "tracks, from", self.sortedKeys[0], "to", self.sortedKeys[-1]

    def updateFromXML(self, fnames, tz = None):
        if len(fnames) == 0: return
        totTime = 0.0
        totDist = 0.0
        print>>sys.stderr, "Updating from xml files... "
        for fname in fnames: 
            track = Track.fromXMLFile(fname, tz)[0]
            if track == None: continue
            startTime = track.getStartTimeAsStr()
            if startTime in self.data: continue
            totDist += track.dist
            totTime += track.duration
            self.data[startTime] = track
            print>>sys.stderr, "Added new track", startTime
        if totTime > 0: 
            hours = int(totTime) / int(60)
            mins = totTime - hours * 60
            print>>sys.stderr, "Updated %.2f miles, %.0f hrs %.0f mins" % (totDist, hours, mins)
        else: print>>sys.stderr, "No tracks added"
        self.sortedKeys = sorted(self.data.keys())

    def getEfficiencies(self):
        effs = []
        for track in self: effs.append(track.efficiency)
        return effs

    def getElevRates(self):
        elevRates = []
        for track in self: elevRates.append(track.elevRate)
        return elevRates
    
    def write(self, outFile, name = "all"):
        Track.writeHeader(outFile)
        for track in self:
            if name == "all" or name == track.getStartTimeAsStr(): track.write(outFile)

    def __iter__(self):
        self.index = 0
        return self

    def next(self):
        if self.index == len(self.sortedKeys) - 1: raise StopIteration
        self.index += 1
        return self.data[self.sortedKeys[self.index]]



