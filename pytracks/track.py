import string, os, sys
import matplotlib.pyplot as pyplot
from datetime import datetime as dt
from xmltree import XMLTree
from courses import Courses
from trackpoints import Trackpoints, Trackpoint

class Track:
    def __init__(self, startTime, duration, dist, maxPace, maxHR, avHR, trackpoints, course, comment):
        self.startTime = startTime
        self.dist = dist
        self.duration = duration
        self.maxPace = maxPace
        self.maxHR = maxHR
        self.avHR = avHR
        self.trackpoints = trackpoints
        self.course = course
        self.comment = comment

    def fromString(cls, line):
        numFields = 13
        tokens = string.split(line, None, numFields)
        if tokens[1] == "0": tokens[1] = "00:00:00"
        if len(tokens) == numFields: comment = ""
        else: comment = tokens[numFields].rstrip()
        return cls(startTime = dt.strptime(tokens[0] + tokens[1], "%Y-%m-%d%H:%M:%S"),
                   dist = float(tokens[2]), 
                   duration = float(tokens[4]), 
                   maxPace = float(tokens[5]),
                   maxHR = float(tokens[7]), 
                   avHR = float(tokens[8]),
                   trackpoints = None,
                   course = tokens[12],
                   comment = comment)
    fromString = classmethod(fromString)

    def fromXMLFile(cls, fname):
        # load the xml file into a tree
        xmlTree = XMLTree(fname)
        # for some reason, the date/time in the file is GMT whereas the file name is local, 
        # so we use the file name
        #self.setStartTime(dt.strptime(tree.find("Activity/Id").text, "%Y-%m-%dT%H:%M:%SZ"))
        startTime = Track.getTimeFromFname(fname)
        durations = xmlTree.findAll("TotalTimeSeconds")
        duration = sum(durations) / 60.0
        # drop point if the tracktime is too small
        if duration <= 5: 
            print>>sys.stderr, "Dropping", fname, "time is < 5 mins"
            return None
        try:
            maxPace = max(xmlTree.findAll("MaximumSpeed"))
        except:
            maxPace = 0
        if maxPace > 0: maxPace = 60.0 / (maxPace * Trackpoints.METERS_PER_MILE / 1000.0)
        dist = sum(xmlTree.findAll("DistanceMeters")) / Trackpoints.METERS_PER_MILE
        # drop point if the dist is measured, but small
        if dist > 0 and dist < 1.0: 
            print>>sys.stderr, "Dropping", fname, "distance is > 0 and < 1.0"
            return None
        maxHRs = xmlTree.findAll("MaximumHeartRateBpm/Value")
        if len(maxHRs) > 0: maxHR = max(maxHRs)
        else: maxHR = 0
        avHRs = xmlTree.findAll("AverageHeartRateBpm/Value")
        avHR = sum([avHRs[i] * durations[i] / 60 for i in range(0, len(avHRs))]) / duration
        # drop all points that have low heart rates
        if avHR < 80 and avHR > 0: 
            print>>sys.stderr, "Dropping", fname, "av HR is < 80 and > 0"
            return None
        # extract trackpoints from xml
        trackpoints = Trackpoints.fromXML(xmlTree, fname)
        # FIXME: try to find a matching course, ask if it is the correct one, or to name the course otherwise
        # FIXME: add an input option to add a comment
        return cls(startTime = startTime, duration = duration, dist = dist, 
                   maxPace = maxPace, maxHR = maxHR, avHR = avHR, trackpoints = trackpoints, 
                   course = "0", comment = "")
    fromXMLFile = classmethod(fromXMLFile)

    def update(self, track):
        self.startTime = track.startTime
        self.dist = track.dist
        self.duration = track.duration
        self.maxPace = track.maxPace
        self.maxHR = track.maxHR
        self.avHR = track.avHR
        self.trackpoints = track.trackpoints
        # don't change course or comments

    def write(self, outFile, useGps):
        dist = 0
        elev = 0
        elevRate = 0
        realDist = 0
        avPace = 0
        efficiency = 0
        if self.course in Courses.data: realDist = Courses.data[self.course].dist
        elev = self.getElevChange(useGps)
        dist = self.getDist(useGps)
        if useGps:
            if dist == 0: dist = realDist
            if elev == 0: elev = self.getElevChange(False)
        else:
            if dist == 0: dist = self.getDist(True)
            if elev == 0: elev = self.getElevChange(True) 

        if dist > 0:
            avPace = self.duration / dist
            elevRate = elev / dist
        if self.avHR > 0 and self.duration > 0:
            efficiency = dist * Trackpoints.METERS_PER_MILE / (self.avHR * self.duration)

        print >> outFile, \
            "%-18s" % self.startTime,\
            "%5.2f" % self.dist,\
            "%5.2f" % realDist,\
            "%6.1f" % self.duration,\
            "%5.2f" % self.maxPace,\
            "%5.2f" % avPace,\
            "%5.0f" % self.maxHR,\
            "%5.0f" % self.avHR,\
            "%5.0f" % elev,\
            "%5.0f" % elevRate,\
            "%5.2f" % efficiency,\
            "%4s" % self.course,\
            " %s " % self.comment

    def writeHeader(cls, outFile):
        print >> outFile, "#%-18s" % "Date & time",\
            "%5s" % "dist",\
            "%5s" % "rdist",\
            "%6s" % "rtime",\
            "%5s" % "mxPc",\
            "%5s" % "avPc",\
            "%5s" % "mxHR",\
            "%5s" % "avHR",\
            "%5s" % "elev",\
            "%5s" % "eRate",\
            "%5s" % "eff",\
            "%4s" % "crs",\
            " %s " % "comment"
    writeHeader = classmethod(writeHeader)

    def getDist(self, useGps):
        dist = 0
        if self.course in Courses.data: dist = Courses.data[self.course].dist
        if useGps and self.dist > 0: dist = self.dist
        return dist

    def getDate(self):
        return self.startTime.strftime("%Y-%m-%d")

    def getGoogleImage(self):
        pngFname = "data/" + self.getStartTimeAsStr() + ".tcx.png"
        if self.trackpoints != None and not os.path.exists(pngFname):
            self.trackpoints.getGoogleMap(pngFname)
        return pyplot.imread(pngFname)

    def getTimeFromFname(cls, fname):
        return dt.strptime(os.path.basename(fname), "%Y-%m-%d-%H%M%S.tcx")
    getTimeFromFname = classmethod(getTimeFromFname)

    def getStartTimeAsStr(self):
        return self.startTime.strftime("%Y-%m-%d-%H%M%S")

    def getElevChange(self, useGps):
        elev = 0
        gpsElevChange = 0
        if self.trackpoints != None: 
            (gpsElevChange, mapElevChange) = self.trackpoints.getElevChanges()
            elev = mapElevChange
        if self.course in Courses.data: 
            elev = Courses.data[self.course].elevChange
        if useGps and gpsElevChange > 0: elev = gpsElevChange
        return elev
        
