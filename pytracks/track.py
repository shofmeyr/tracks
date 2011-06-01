import string, os, sys
import matplotlib.pyplot as pyplot
import datetime
from courses import Courses
from trackpoints import Trackpoints, Trackpoint
from xmltree import XMLTree
import pytz

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

    def __len__(self):
        return len(self.trackpoints)

    def __getitem__(self, key):
        return self.trackpoints[key]

    def __setitem__(self, key, value):
        self.trackpoints[key] = value

    @classmethod
    def fromXMLFile(cls, fname, tz = None):
        # load the xml file into a tree
        tree = XMLTree(fname, namespace = {"t":"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}, 
                       root = "t:Activities/t:Activity/")
        utcStartTime = tree.findAll("t:Id", isFloat = False)[0]
        comment = tree.findAll("t:Comment", isFloat = False)
        if len(comment) > 0: comment = comment[0]
        else: comment = ""
        course = tree.findAll("t:Course", isFloat = False)
        if len(course) > 0: course = course[0]
        else: course = 0
        tree.root += "t:Lap/"
        durations = tree.findAll("t:TotalTimeSeconds")
        duration = sum(durations) / 60.0
        # drop point if the tracktime is too small
        if duration <= 5: 
            print>>sys.stderr, "Dropping", fname, "time is < 5 mins"
            return None
        try:
            maxPace = max(tree.findAll("t:MaximumSpeed"))
        except:
            maxPace = 0
        if maxPace > 0: maxPace = 60.0 / (maxPace * Trackpoints.METERS_PER_MILE / 1000.0)
        dist = sum(tree.findAll("t:DistanceMeters")) / Trackpoints.METERS_PER_MILE
        # drop point if the dist is measured, but small
        if dist > 0 and dist < 1.0: 
            print>>sys.stderr, "Dropping", fname, "distance is > 0 and < 1.0"
            return None
        maxHRs = tree.findAll("t:MaximumHeartRateBpm/t:Value")
        if len(maxHRs) > 0: maxHR = max(maxHRs)
        else: maxHR = 0
        avHRs = tree.findAll("t:AverageHeartRateBpm/t:Value")
        avHR = sum([avHRs[i] * durations[i] / 60 for i in range(0, len(avHRs))]) / duration
        # drop all points that have low heart rates
        if avHR < 80 and avHR > 0: 
            print>>sys.stderr, "Dropping", fname, "av HR is < 80 and > 0"
            return None
        # extract trackpoints from xml
        trackpoints = Trackpoints.fromXML(tree, fname)
        # FIXME: try to find a matching course, ask if it is the correct one, or to name the course otherwise
        # FIXME: add an input option to add a comment
        # now write the modified tree back to the file
        f = open(fname, "w")
        tree.write(f)
        f.close()
        # time is UTC, try to convert it here
        lng = None
        if len(trackpoints) > 0: lng =  trackpoints[0].lng
        startTime = Track.getLocalTime(utcStartTime, lng, tz)
        return (cls(startTime = startTime, duration = duration, dist = dist, 
                    maxPace = maxPace, maxHR = maxHR, avHR = avHR, trackpoints = trackpoints, 
                    course = course, comment = comment), tree)

    @classmethod
    def getLocalTime(cls, utcTimeStr, lng, tz):
        # FIXME: the time is given as UTC. What is needed is a way to convert the time to the correct one for
        # the geographic location, as given by the gps coordinates. We use something very simple here which
        # gives an approximation of the actual time. A better way to do this is use a timezone service.
        # This can always be corrected later.
        utcTime = datetime.datetime.strptime(utcTimeStr, "%Y-%m-%dT%H:%M:%SZ")
#        print "utcTime", utcTime
        utcTime = utcTime.replace(tzinfo=pytz.utc)
#        print "UTC replaced", utcTime
        if tz != None and tz != "": localTime = utcTime.astimezone(pytz.timezone(tz))
        elif lng != None: localTime = utcTime + datetime.timedelta(hours = int(round(lng / 15.0)))
        else: localTime = utcTime
#        print "Local time", str(localTime)
        return localTime

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
            "%-18s" % self.startTime.strftime("%Y-%m-%d %H:%M:%S"),\
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

    @classmethod
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

    def getDist(self, useGps):
        dist = 0
        if self.course in Courses.data: dist = Courses.data[self.course].dist
        if useGps and self.dist > 0: dist = self.dist
        return dist

    def getDate(self):
        return self.startTime.strftime("%Y-%m-%d")

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
        
    def getMidPointRange(self, t):
        if t == "lats": x = self.trackpoints.getLats()
        else: x = self.trackpoints.getLngs()
        minX = min(x)
        maxX = max(x)
        return (minX + (maxX - minX) / 2.0, maxX - minX)

