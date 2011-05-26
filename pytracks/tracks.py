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

    def load(self, fname, textFname):
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
        if textFname != "": self.loadAdditionalFromText(textFname)

    def loadAdditionalFromText(self, textFname):
        # below is my crude hack to input course and comments from a text file. Will be removed when other 
        # editing functionality is added. 
        f = open(textFname, "r")
        if f == None: return
        found = None
        num = 0
        for line in f.readlines():
            if line.strip() == "": continue
            if line.lstrip()[0] == "#": 
                if found != None: found.comment += "\n" + line.rstrip()
                continue
            savedTrack = Track.fromString(line)
            found = None
            for track in self.data.values():
                if savedTrack.startTime == track.startTime: 
                    track.course = savedTrack.course
                    track.comment = savedTrack.comment
                    found = track
                    num += 1
                    break
            if found == None: 
                self.data[savedTrack.getStartTimeAsStr()] = savedTrack
                num += 1
        print>>sys.stderr, "Loaded additional data for", num, "tracks from \"" + textFname + "\""
        f.close()

    def save(self, fname):
        if fname == "": return
        try:
            f = open(fname, "w+")
            pickle.dump(self.data, f)
            f.close()
        except Exception as e:
            print>>sys.stderr, "Could not save data in " + fname + ": " + str(e)
            return
        print>>sys.stderr, "Saved data for", len(self.data), " tracks, from", \
            self.getSortedTracks()[0].startTime, "to", self.getSortedTracks()[-1].startTime

    def updateFromXML(self, fnames):
        if len(fnames) == 0: return
        totTime = 0.0
        totDist = 0.0
        print>>sys.stderr, "Updating from xml files... "
        for fname in fnames: 
            trackId = os.path.basename(fname)
            if trackId in self.data: continue
            track = Track.fromXMLFile(fname)
            if track == None: continue
            totDist += track.dist
            totTime += track.duration
            self.data[trackId] = track
            print "Found new track", track.getStartTimeAsStr()
        if totTime > 0: print>>sys.stderr, "Updated %.2f miles, %.1f mins" % (totDist, totTime)
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



