import string, os, sys
import datetime
from trackpoints import Trackpoints

class Track:
    def __init__(self, startTime, duration, dist, maxPace, maxHR, avHR, trackpoints, comment,
                 knownElev = 0, knownDist = 0):
        self.startTime = startTime
        self.dist = dist
        self.duration = duration
        self.maxPace = maxPace
        self.maxHR = maxHR
        self.avHR = avHR
        self.trackpoints = trackpoints
        self.comment = comment
        self.knownElev = knownElev
        self.knownDist = knownDist

    def __len__(self):
        return len(self.trackpoints)

#    def __getitem__(self, key):
#        return self.trackpoints[key]

#    def __setitem__(self, key, value):
#        self.trackpoints[key] = value

    @classmethod
    def fromXMLFile(cls, fname, tz = None):
        from xmltree import XMLTree
        # load the xml file into a tree
        tree = XMLTree(fname, namespace = 
                       {"t":"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}, 
                       root = "t:Activities/t:Activity/")
        utcStartTime = tree.findAll("t:Id", isFloat = False)[0]
        comment = tree.findAll("t:Comment", isFloat = False)
        if len(comment) > 0: comment = comment[0]
        else: comment = ""
        knownElev = tree.findAll("t:KnownElevationMeters")
        if len(knownElev) > 0: knownElev = knownElev[0]
        else: knownElev = 0
        knownDist = tree.findAll("t:KnownDistanceMeters")
        if len(knownDist) > 0: knownDist = knownDist[0]
        else: knownDist = 0

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
        if dist == 0: dist = knownDist / Trackpoints.METERS_PER_MILE
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
        trackpoints = Trackpoints()
        trackpoints.loadFromXML(tree, fname)
        # FIXME: add an input option to add a comment
        # now write the modified tree back to the file
        f = open(fname, "w")
        tree.write(f)
        f.close()
        # time is UTC, try to convert it here
        lng = None
        if len(trackpoints) > 0: lng =  trackpoints.lngs[0]
        startTime = Track.getLocalTime(utcStartTime, lng, tz)
        return (cls(startTime = startTime, duration = duration, dist = dist, 
                    maxPace = maxPace, maxHR = maxHR, avHR = avHR, trackpoints = trackpoints, 
                    comment = comment, knownElev = knownElev, knownDist = knownDist), tree)

    @classmethod
    def getLocalTime(cls, utcTimeStr, lng, tz):
        import pytz
        # FIXME: the time is given as UTC. What is needed is a way to convert the time to the 
        # correct one for the geographic location, as given by the gps coordinates. We use 
        # something very simple here which gives an approximation of the actual time. A better way 
        # to do this is use a timezone service.
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

    def write(self, outFile, elevWindow, timeStr = None):
        elev = 0
        elevRate = 0
        avPace = 0
        efficiency = 0
        elev = self.getElevChange(elevWindow)
        if self.dist > 0:
            avPace = self.duration / self.dist
            elevRate = elev / self.dist
        if self.avHR > 0 and self.duration > 0:
            efficiency = self.dist * Trackpoints.METERS_PER_MILE / (self.avHR * self.duration)

        if timeStr == None: timeStr = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        print >> outFile, \
            "%-20s" % timeStr,\
            "%6.2f" % self.dist,\
            "%7.1f" % self.duration,\
            "%5.2f" % self.maxPace,\
            "%5.2f" % avPace,\
            "%5.0f" % self.maxHR,\
            "%5.0f" % self.avHR,\
            "%6.0f" % elev,\
            "%6.0f" % (self.knownElev * Trackpoints.FEET_PER_METER),\
            "%5.0f" % elevRate,\
            "%5.2f" % efficiency,\
            " %s " % self.comment

    @classmethod
    def writeHeader(cls, outFile):
        print >> outFile, "#%-19s" % "Date & time",\
            "%6s" % "dist",\
            "%7s" % "rtime",\
            "%5s" % "mxPc",\
            "%5s" % "avPc",\
            "%5s" % "mxHR",\
            "%5s" % "avHR",\
            "%6s" % "elev",\
            "%6s" % "kElev",\
            "%5s" % "eRate",\
            "%5s" % "eff",\
            " %s " % "comment"

    def getDate(self):
        return self.startTime.strftime("%Y-%m-%d")

    def getStartTimeAsStr(self):
        return self.startTime.strftime("%Y-%m-%d-%H%M%S")

    def getElevChange(self, smoothingWindow):
        elevChange = 0
        if self.trackpoints != None: elevChange = self.trackpoints.getElevChange(smoothingWindow)
        if elevChange == 0: return self.knownElev * Trackpoints.FEET_PER_METER
        return elevChange
        
    def getMidPointRange(self, t):
        if t == "lats": x = self.trackpoints.lats
        else: x = self.trackpoints.lngs
        minX = min(x)
        maxX = max(x)
        return (minX + (maxX - minX) / 2.0, maxX - minX)

