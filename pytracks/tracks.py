#!/usr/bin/python -u 

import sys, pickle, os
from track import Track
from trackpoints import Trackpoints

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
        else: 
            print>>sys.stderr, "Loaded", len(self.data), "tracks from \"" + fname + "\":",\
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
    
    def write(self, outFile, name = "all", elevWindow = 2):
        Track.writeHeader(outFile)
        trackTot = Track(startTime = None, duration = 0, dist = 0, maxPace = 0, maxHR = 0,
                         avHR = 0, trackpoints = None, comment = "", knownElev = 0)
        numTracksForHR = 0.0
        for track in self:
            if name == track.getStartTimeAsStr()[:len(name)]: 
                if trackTot.startTime == None: trackTot.startTime = track.startTime
                trackTot.duration += track.duration
                trackTot.dist += track.dist
                if track.maxPace > trackTot.maxPace: trackTot.maxPace = track.maxPace
                if track.maxHR > trackTot.maxHR and track.maxHR < 190: trackTot.maxHR = track.maxHR
                trackTot.avHR += track.avHR
                if track.avHR > 0: numTracksForHR += 1
                trackTot.knownElev += (track.getElevChange(elevWindow) / Trackpoints.FEET_PER_METER)
                track.write(outFile, elevWindow)
        # now print summary
        trackTot.avHR /= numTracksForHR
        trackTot.write(outFile, elevWindow, name)

    def __iter__(self):
        self.index = 0
        return self

    def next(self):
        if self.index == len(self.sortedKeys) - 1: raise StopIteration
        self.index += 1
        return self.data[self.sortedKeys[self.index]]

    def getMonthlyStats(self):
        months = []
        dists = []
        paces = []
        hrs = []
        durations = []
        i = 0
        dist = 0
        duration = 0
        hr = 0
        numHrs = 0
        for m in self:
            monthStr = m.startTime.strftime("%Y-%m")
            if i == 0: months.append(monthStr)
            elif months[-1] != monthStr: 
                months.append(monthStr)
                dists.append(dist)
                paces.append(duration)
                hrs.append(hr / numHrs)
                durations.append(duration)
                dist = 0
                duration = 0
                hr = 0
                numHrs = 0
            else:
                if m.dist > 0:
                    dist += m.dist
                    duration += m.duration
                if m.avHR > 0:
                    hr += m.avHR
                    numHrs += 1
            i += 1
        for i in range(0, len(paces)): 
            if dists[i] > 0: paces[i] /= dists[i]
            else: paces[i] = 10
        return (months, dists, paces, hrs, durations)

        


