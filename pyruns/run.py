import string, os
#import Image, pylab
import matplotlib.pyplot as pyplot
from datetime import datetime as dt
from coords import Coords
from xmltree import XMLTree
from courses import Courses

class Run:
    useGpsElev = False
    useGpsDist = False

    def __init__(self, startTime, duration, dist, realDist, maxPace, maxHR,
                 avHR, elevChange, course, comment):
        self.startTime = startTime
        self.dist = dist
        self.realDist = realDist
        self.duration = duration
        self.maxPace = maxPace
        self.maxHR = maxHR
        self.avHR = avHR
        self.elevChange = elevChange
        self.coords = None
        self.course = course
        self.comment = comment
        # now we update elev and realDist according to the course
        if self.course in Courses.data:
            if not Run.useGpsElev: self.elevChange = Courses.data[self.course].elevChange
            self.realDist = Courses.data[self.course].dist
        if Run.useGpsDist: dist = self.dist
        if dist == 0: dist = self.realDist
        if dist > 0:
            self.avPace = self.duration / dist
            if self.avHR > 0: 
                self.efficiency = Coords.METERS_PER_MILE / (self.avHR * self.duration / dist)
            else: self.efficiency = 0
        else: 
            self.avPace = 0
            self.efficiency = 0
        # for comparing elevations
        # check to see if there is a file for elevations
        elevFname = self.startTime.strftime("data/%Y-%m-%d-%H%M%S.tcx.coords")
        if os.path.exists(elevFname): 
            self.coords = Coords.fromFile(elevFname)
            print self.startTime, "%.0f mins," % self.duration, "%.2f miles," % self.dist,\
                "%.0f ft (gps)," % self.coords.gpsChange, "%.0f ft (map)," % self.coords.mapChange, 
            if self.course in Courses.data and Courses.data[self.course].elevChange > 0: 
                print "%.0f miles (course)" % Courses.data[self.course].dist,
                "%.0f ft (course)" % Courses.data[self.course].elevChange, 
            else: print "course %s," % self.course
            if self.elevChange == 0 or Run.useGpsElev: self.elevChange = self.coords.mapChange
        if self.elevChange > 0 and dist > 0: self.elevRate = self.elevChange / dist
        else: self.elevRate = 0

    def fromString(cls, line):
        numFields = 13
        tokens = string.split(line, None, numFields)
        if tokens[1] == "0": tokens[1] = "00:00:00"
        if len(tokens) == numFields: comment = ""
        else: comment = tokens[numFields].rstrip()
        return cls(startTime = dt.strptime(tokens[0] + tokens[1], "%Y-%m-%d%H:%M:%S"),
                   dist = float(tokens[2]), 
                   realDist = float(tokens[3]),
                   duration = float(tokens[4]), 
                   maxPace = float(tokens[5]),
                   maxHR = float(tokens[7]), 
                   avHR = float(tokens[8]), 
                   elevChange = float(tokens[9]),
                   course = tokens[12],
                   comment = comment)
    fromString = classmethod(fromString)

    def fromXMLFile(cls, fname):
        # load the xml file into a tree
        xmlTree = XMLTree(fname)
        # for some reason, the date/time in the file is GMT whereas the file name is local, 
        # so we use the file name
        #self.setStartTime(dt.strptime(tree.find("Activity/Id").text, "%Y-%m-%dT%H:%M:%SZ"))
        startTime = Run.getTimeFromFname(fname)
        durations = xmlTree.findAll("TotalTimeSeconds")
        duration = sum(durations) / 60.0
        # drop point if the runtime is too small
        if duration <= 5: return None
        maxPace = max(xmlTree.findAll("MaximumSpeed"))
        if maxPace > 0: maxPace = 60.0 / (maxPace * Coords.METERS_PER_MILE / 1000.0)
        dist = sum(xmlTree.findAll("DistanceMeters")) / Coords.METERS_PER_MILE
        # drop point if the dist is measured, but small
        if dist > 0 and dist < 1.0: return None
        maxHRs = xmlTree.findAll("MaximumHeartRateBpm/Value")
        if len(maxHRs) > 0: maxHR = max(maxHRs)
        else: maxHR = 0
        avHRs = xmlTree.findAll("AverageHeartRateBpm/Value")
        avHR = sum([avHRs[i] * durations[i] / 60 for i in range(0, len(avHRs))]) / duration
        # drop all points that have low heart rates
        if avHR < 80 and avHR > 0: return None
        # check to see if there is a file for elevations
        elevFname = fname + ".coords"
        if os.path.exists(elevFname): coords = Coords.fromFile(elevFname)
        else: 
            print "fetching elevations from google for", fname, "..."
            # get coords if we have the trackpoints
            coords = Coords.fromTrackpoints(
                xmlTree.findAll("Track/Trackpoint/Position/LatitudeDegrees"),
                xmlTree.findAll("Track/Trackpoint/Position/LongitudeDegrees"),
                xmlTree.findAll("Track/Trackpoint/DistanceMeters"),
                xmlTree.findAll("Track/Trackpoint/AltitudeMeters"))
            # save the elevations to file
            f = open(elevFname, "w+")
            coords.write(f)
            f.close()
        # FIXME: try to find a matching course, ask if it is the correct one, or to name the course otherwise
        # FIXME: add an input option to add a comment
        return cls(startTime = startTime, duration = duration, dist = dist, realDist = 0,
                   maxPace = maxPace, maxHR = maxHR, avHR = avHR, elevChange = 0, course = "0", comment = "")
    fromXMLFile = classmethod(fromXMLFile)

    def update(self, run):
        self.startTime = run.startTime
        self.dist = run.dist
        self.realDist = run.realDist
        self.duration = run.duration
        self.maxPace = run.maxPace
        self.maxHR = run.maxHR
        self.avHR = run.avHR
        self.elevChange = run.elevChange
        self.coords = run.coords
        # don't change course or comments

    def write(self, outFile):
        print >> outFile, "%-18s" % self.startTime,\
            "%5.2f" % self.dist,\
            "%5.2f" % self.realDist,\
            "%6.1f" % self.duration,\
            "%5.2f" % self.maxPace,\
            "%5.2f" % self.avPace,\
            "%5.0f" % self.maxHR,\
            "%5.0f" % self.avHR,\
            "%5.0f" % self.elevChange,\
            "%5.0f" % self.elevRate,\
            "%5.2f" % self.efficiency,\
            "%4s" % self.course,\
            " %s " % self.comment
        
    def getDate(self):
        return self.startTime.strftime("%Y-%m-%d")

    def getGoogleImage(self):
        pngFname = self.startTime.strftime("data/%Y-%m-%d-%H%M%S.tcx.png")
        if self.coords != None and not os.path.exists(pngFname):
            self.coords.getGoogleMap(pngFname)
        return pyplot.imread(pngFname)

    def getTimeFromFname(cls, fname):
        return dt.strptime(os.path.basename(fname), "%Y-%m-%d-%H%M%S.tcx")
    getTimeFromFname = classmethod(getTimeFromFname)
