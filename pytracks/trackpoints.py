import numpy, sys, simplejson, urllib, os
from xmltree import XMLTree

class Trackpoint:
    def __init__(self, tm, lat, lng, dist = 0, gpsElev = 0, mapElev = 0, hr = 0):
        self.time = tm
        self.lat = lat
        self.lng = lng
        self.dist = dist
        self.gpsElev = gpsElev
        self.mapElev = mapElev
        self.hr = hr

    def getUrlLatLng(self):
        return str(self.lat) + "," + str(self.lng)


class Trackpoints:
    METERS_PER_MILE = 1609.344
    FEET_PER_METER = 3.28084
    elevWindow = 5

    def __init__(self, points):
        self.points = points

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

    def getElevChanges(self):
        # smooth the elevations
        gpsSmoothed = []
        mapSmoothed = []
        for i in range(0, len(self.points) - Trackpoints.elevWindow): 
            gpsSmoothed.append(numpy.average([p.gpsElev for p in self.points[i:i + Trackpoints.elevWindow]]))
            mapSmoothed.append(numpy.average([p.mapElev for p in self.points[i:i + Trackpoints.elevWindow]]))
        # compute elevation change
        gpsChange = 0
        mapChange = 0
        for i in range(0, len(gpsSmoothed) - 1):
            gpsChange += self.computeChange(gpsSmoothed[i + 1], gpsSmoothed[i])
            mapChange += self.computeChange(mapSmoothed[i + 1], mapSmoothed[i])
        gpsChange *= Trackpoints.FEET_PER_METER
        mapChange *= Trackpoints.FEET_PER_METER
        return (gpsChange, mapChange)

    def getMinMaxElevs(self, useGps = False):
        minElev = 30000.0
        maxElev = 0.0
        for point in self.points:
            if useGps:
                minElev = min(point.gpsElev, minElev)
                maxElev = max(point.gpsElev, maxElev)
            else:
                minElev = min(point.mapElev, minElev)
                maxElev = max(point.mapElev, maxElev)
        return (minElev * Trackpoints.FEET_PER_METER, maxElev * Trackpoints.FEET_PER_METER)

    def computeChange(self, first, second):
        change = first - second
        if change < 0: change = 0
        return change

    def fromXML(cls, tree, fname):
        root = "t:Track/t:Trackpoint/"
        times = tree.findAll(root + "t:Time", False)
        lats = tree.findAll(root + "t:Position/t:LatitudeDegrees")
        lngs = tree.findAll(root + "t:Position/t:LongitudeDegrees")
        dists = tree.findAll(root + "t:DistanceMeters")
        altitudes = tree.findAll(root + "t:AltitudeMeters")
        hrs = tree.findAll(root + "t:HeartRateBpm/t:Value")
        mapAltitudes = tree.findAll(root + "t:MapAltitudeMeters")
        points = []
        if not (len(times) >= len(lats) == len(lngs) == len(dists) == len(altitudes) == len(hrs)): 
            print>>sys.stderr, "Missing points in xml file", fname, ":",\
                "times", len(times), "lats", len(lats), "lngs", len(lngs), "dists", len(dists),\
                "altitudes", len(altitudes), "hrs", len(hrs)
        if len(mapAltitudes) == 0 and len(altitudes) > 0:
            # no previous elevations, fetch from google
            if not os.path.exists(fname + ".elev"): mapAltitudes = Trackpoints.getGoogleElevs(lats, lngs)
            else: mapAltitudes = Trackpoints.readElevsFile(fname + ".elev")
            # add the elevs to the xmltree
            print>>sys.stderr, "Adding", len(mapAltitudes), "map elevations to", fname
            tree.addElems("t:Track/t:Trackpoint", "MapAltitudeMeters", mapAltitudes, "AltitudeMeters")
        # set up the points array
        for i in range(0, min(len(lats), len(lngs))):
            if len(hrs) <= i: hrs.append(0)
            if len(altitudes) <= i: altitudes.append(0)
            if len(dists) <= i: dists.append(0)
            points.append(Trackpoint(tm = times[i], lat = lats[i], lng = lngs[i], 
                                     dist = dists[i] / Trackpoints.METERS_PER_MILE, gpsElev = altitudes[i], 
                                     mapElev = mapAltitudes[i], 
                                     hr = hrs[i]))
        return cls(points)
    fromXML = classmethod(fromXML)

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
    readElevsFile = classmethod(readElevsFile)

        # check to see if there is already a file for elevations
#        elevFname = fname + ".elev"
#        if not os.path.exists(elevFname): 
#            if len(points) > 0:
#                # save the elevations to file
#                f = open(elevFname, "w+")
#                for point in points: print>>f, point.lat, point.lng, point.dist, point.gpsElev, point.mapElev
#                f.close()
        # else:
        #     # previous elevs file, load up
        #     f = open(elevFname, "r")
        #     i = 0
        #     for line in f.readlines(): 
        #         tokens = line.lstrip().rstrip().split()
        #         lat = float(tokens[0])
        #         lng = float(tokens[1])
        #         mapElev = float(tokens[4])
        #         if lat != points[i].lat or lng != points[i].lng:
        #             print>>sys.stderr, "Mismatch between points at index", i, "in file", elevFname,\
        #                 lat, points[i].lat, lng, points[i].lng
        #             break
        #         points[i].mapElev = mapElev
        #         i += 1
        #     f.close()

    def write(self, outFile):
        for point in self.points: print>>outFile, point.lat, point.lng, point.dist, point.gpsElev, point.mapElev

    # this is taken from a google eg at 
    # http://gmaps-samples.googlecode.com/svn/trunk/elevation/python/ElevationChartCreator.py
    # The maximum length URL that can be submitted is 2048. Now a location takes 22 chars,
    # so with the base, the maximum number of points that can be submitted in one request 
    # is 90 
    # The usage limits constrain us to 2500 request per day or 25000 locations
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
                # print url
                # print "sending url of length", (baseUrlLen + len(path)), len(url)
                response = simplejson.load(urllib.urlopen(url))
                # print response
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
    getGoogleElevs = classmethod(getGoogleElevs)

    def getGoogleMap(self, fname):
        print "Getting map from Google for course", fname
        # the url is limited to length 2048. the header is 127 chars, and each point is 28 chars, so we are limited to
        # about 68 points
        urlBase = "https://maps.googleapis.com/maps/api/staticmap?"
        sampleInterval = len(self.points) / 60
        path = ""
        for i in range(0, len(self.points), sampleInterval):
            if path != "": path += "|"
            path += self.points[i].getUrlLatLng()
        path += "|" + self.points[-1].getUrlLatLng()
        url = urlBase + urllib.urlencode({"sensor": "false", "size": "1000x1000", "maptype": "terrain", 
                                          "path": "weight:2|color:0xFF0000|" + path})
        response = (urllib.urlopen(url))
        f = open(fname, "w+")
        f.write(response.read())
        f.close()

    def getDists(self):
        dists = []
        for point in self.points: dists.append(point.dist)
        return dists

    def getMapElevs(self):
        elevs = []
        for point in self.points: elevs.append(point.mapElev * Trackpoints.FEET_PER_METER)
        return elevs
    
    def getLats(self):
        lats = []
        for point in self.points: lats.append(point.lat)
        return lats
    
    def getLngs(self):
        lngs = []
        for point in self.points: lngs.append(point.lng)
        return lngs


