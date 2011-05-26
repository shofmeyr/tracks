#!/usr/bin/python -u 

import sys, pickle, os

from track import Track
from courses import Courses
from datetime import datetime as dt

class Tracks:
    def __init__(self):
        self.tracks = {}

    def load(self, fnames):
        # each track is stored in a separate pickle file 
        f = None
        if os.path.exists(fname + ".pck"): f = open(fname + ".pck", "r")
        if f != None:
            self.tracks = pickle.load(f)
            f.close()
        if len(self.tracks) == 0: print "Found no saved tracks"
        else: print "Loaded data from", self.getSortedTracks()[0].startTime, "to", self.getSortedTracks()[-1].startTime
        
        return
        # below is my crude hack to input course and comments from a text file. Will be removed when other 
        # editing functionality is added
        f = open("summary.dat", "r")
        found = None
        for line in f.readlines():
            if line.strip() == "": continue
            if line.lstrip()[0] == "#": 
                if found != None: found.comment += "\n" + line.rstrip()
                continue
            savedTrack = Track.fromString(line)
            found = None
            for track in self.tracks.values():
                if savedTrack.startTime == track.startTime: 
                    print "found track", savedTrack.startTime, "in the file"
                    track.course = savedTrack.course
                    track.comment = savedTrack.comment
                    found = track
                    break
            if found == None: self.tracks[savedTrack.getStartTimeAsStr()] = savedTrack
        f.close()

    def save(self, fname):
        f = open(fname + ".pck", "w+")
        pickle.dump(self.tracks, f)
        f.close()
        print "Saved data from", self.getSortedTracks()[0].startTime, "to", self.getSortedTracks()[-1].startTime

    def updateFromXML(self, fnames):
        totTime = 0.0
        totDist = 0.0
        print "Updating... "
        skipAll = False
        for fname in fnames: 
            trackId = os.path.basename(fname)
            update = False
            if trackId in self.tracks:
                if skipAll: continue
                print "Found track", trackId, "corresponding to:"
                self.tracks[trackId].write(sys.stdout, "all")
                answer = raw_input("Would you like to update? (y)es/(N)o/(s)kip all ")
                if answer == "": continue
                if answer.lower() == "n": continue
                if answer.lower() == "s": skipAll = True
                else: update = True
            track = Track.fromXMLFile(fname)
            if track == None: continue
            totDist += track.dist
            totTime += track.duration
            if update: self.tracks[trackId].update(track)
            else: self.tracks[trackId] = track
        if totTime > 0: print "Updated %.2f miles, %.1f mins" % (totDist, totTime)
        else: print "no tracks added"

    def getSortedTracks(self):
        return sorted(self.tracks.values(), key=lambda track: track.startTime)

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



