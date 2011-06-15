import numpy, sys, simplejson, urllib, os

class Trackpoints:
    METERS_PER_MILE = 1609.344
    FEET_PER_METER = 3.28084
    elevWindow = 5

    def __init__(self):
        self.times = []
        self.lats = []
        self.lngs = []
        self.dists = []
        self.gpsElevs = []
        self.mapElevs = []
        self.hrs = []
        self.length = 0

    def __len__(self):
        return self.length

    def getElevChange(self):
        # smooth the elevations
        smoothedElevs = []
        for i in range(0, len(self) - Trackpoints.elevWindow): 
            smoothedElevs.append(numpy.average(self.mapElevs[i:i + Trackpoints.elevWindow]))
        # compute elevation change
        totChange = 0
        for i in range(0, len(smoothedElevs) - 1):
            change = smoothedElevs[i + 1] - smoothedElevs[i]
            if change < 0: change = 0
            totChange += change
        totChange *= Trackpoints.FEET_PER_METER
        return totChange

    def getMinMaxElevs(self):
        minElev = min(self.mapElevs)
        maxElev = max(self.mapElevs)
        return (minElev * Trackpoints.FEET_PER_METER, maxElev * Trackpoints.FEET_PER_METER)

    def getElevs(self):
        return [e * Trackpoints.FEET_PER_METER for e in self.mapElevs]

    def loadFromXML(self, tree, fname):
        root = "t:Track/t:Trackpoint/"
        self.times = tree.findAll(root + "t:Time", False)
        self.lats = tree.findAll(root + "t:Position/t:LatitudeDegrees")
        self.lngs = tree.findAll(root + "t:Position/t:LongitudeDegrees")
        self.dists = [d / Trackpoints.METERS_PER_MILE 
                      for d in tree.findAll(root + "t:DistanceMeters")]
        self.gpsElevs = tree.findAll(root + "t:AltitudeMeters")
        self.hrs = tree.findAll(root + "t:HeartRateBpm/t:Value")
        self.mapElevs = tree.findAll(root + "t:MapAltitudeMeters")
        if not (len(self.times) >= len(self.lats) == len(self.lngs) == len(self.dists) == 
                len(self.gpsElevs) == len(self.hrs)): 
            print>>sys.stderr, "Missing points in xml file", fname, ":",\
                "times", len(self.times), "lats", len(self.lats), "lngs",\
                len(self.lngs), "dists", len(self.dists),\
                "altitudes", len(self.gpsElevs), "hrs", len(self.hrs)
        self.length = min([len(self.times), len(self.lats), len(self.lngs), len(self.dists), 
                           len(self.gpsElevs), len(self.hrs)])
        if len(self.mapElevs) == 0 and len(self.gpsElevs) > 0:
            # no previous elevations, fetch from google
            if not os.path.exists(fname + ".elev"): 
                self.mapElevs = Trackpoints.getGoogleElevs(lats, lngs)
            else: mapElevs = Trackpoints.readElevsFile(fname + ".elev")
            # add the elevs to the xmltree
            print>>sys.stderr, "Adding", len(self.mapElevs), "map elevations to", fname
            tree.addElems("t:Track/t:Trackpoint", "MapAltitudeMeters", 
                          self.mapElevs, "AltitudeMeters")

    @classmethod
    def readElevsFile(cls, elevFname):
        f = open(elevFname, "r")
        elevs = []
        for line in f.readlines(): 
            tokens = line.lstrip().rstrip().split()
            lat = float(tokens[0])
            lng = float(tokens[1])
            mapElev = float(tokens[4])
            elevs.append(mapElev)
        f.close()
        return elevs

    def write(self, outFile):
        for i in range(0, len(self)):
            print>>outFile, self.lats[i], self.lngs[i], self.dists[i], self.gpsElevs[i], \
                self.mapElevs[i], self.hrs[i]

    # this is taken from a google eg at 
    # http://gmaps-samples.googlecode.com/svn/trunk/elevation/python/ElevationChartCreator.py
    # The maximum length URL that can be submitted is 2048. Now a location takes 22 chars,
    # so with the base, the maximum number of points that can be submitted in one request 
    # is 90 
    # The usage limits constrain us to 2500 request per day or 25000 locations
    @classmethod
    def getGoogleElevs(cls, lats, lngs):
        if len(lats) == 0: return []
        print>>sys.stdout, "Fetching elevations for", len(lats), "points from google"
        ELEV_BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
        baseUrlLen = len(ELEV_BASE_URL) + len("?locations=") + len("&sensor=false")
        path = ""
        elevs = []
        for i in range(0, len(lats)):
            if path != "": path += "|"
            path += str(lats[i]) + "," + str(lngs[i])
            url = ELEV_BASE_URL + '?' + urllib.urlencode({'locations': path, 'sensor': 'false'})
            # cannot have a longer url, so we make the request
            if len(url) > 2048 - 30 or i == len(lats) - 1:
                response = simplejson.load(urllib.urlopen(url))
                if response['status'] != "OK":
                    print>>sys.stderr, "Could not get elevs from Google:", response['status']
                    break
                for resultset in response['results']: elevs.append(float(resultset['elevation']))
                path = ""
        if len(elevs) != len(lats): 
            print>>sys.stderr, "Could not retrieve all", len(lats), "points from google, only got", \
                len(elevs), "-- try again later"
            return []
        return elevs


