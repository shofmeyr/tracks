#!/usr/bin/python -u 

import sys, pickle, os
from track import Track
from courses import Courses

class Tracks:
    def __init__(self):
        self.data = {}

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
            except Exception as e:
                "Could not load pickle file " + fname + ": " + str(e)
        if fname != "" and len(self.data) == 0: print>>sys.stderr, "Found no saved tracks in \"" + fname + "\""
        else: print>>sys.stderr, "Loaded", len(self.data), "tracks from \"" + fname + "\":",\
                self.getSortedTracks()[0].startTime, "to", self.getSortedTracks()[-1].startTime

    def save(self, fname):
        if fname == "": return
        try:
            f = open(fname, "w+")
            pickle.dump(self.data, f)
            f.close()
        except Exception as e:
            print>>sys.stderr, "Could not save data in " + fname + ": " + str(e)
            return
        print>>sys.stderr, "Saved data for", len(self.data), "tracks, from", \
            self.getSortedTracks()[0].startTime, "to", self.getSortedTracks()[-1].startTime

    def updateFromXML(self, fnames, tz = None):
        if len(fnames) == 0: return
        totTime = 0.0
        totDist = 0.0
        print>>sys.stderr, "Updating from xml files... "
        for fname in fnames: 
            trackId = os.path.basename(fname)
            if trackId in self.data: continue
            track = Track.fromXMLFile(fname, tz)[0]
            if track == None: continue
            totDist += track.dist
            totTime += track.duration
            self.data[trackId] = track
            print>>sys.stderr, "Added new track", track.getStartTimeAsStr()
        if totTime > 0: 
            hours = int(totTime) / int(60)
            mins = totTime - hours * 60
            print>>sys.stderr, "Updated %.2f miles, %.0f hrs %.0f mins" % (totDist, hours, mins)
        else: print>>sys.stderr, "No tracks added"

    def getSortedTracks(self):
        return sorted(self.data.values(), key=lambda track: track.startTime)

    def getEfficiencies(self):
        effs = []
        for track in self.getSortedTracks(): effs.append(track.efficiency)
        return effs

    def getElevRates(self):
        elevRates = []
        for track in self.getSortedTracks(): elevRates.append(track.elevRate)
        return elevRates
    
    def write(self, outFile, name = "all", useGps = False):
        Track.writeHeader(outFile)
        for track in self.getSortedTracks(): 
            if name == "all" or name == track.getStartTimeAsStr() or name == track.course:
                track.write(outFile, useGps)



