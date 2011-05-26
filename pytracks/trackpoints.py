import numpy, sys, simplejson, urllib, os

class Trackpoint:
    def __init__(self, tm, lat, lng, dist = 0, gpsElev = 0, mapElev = 0, hr = 0):
        self.time = tm
        self.lat = lat
        self.lng = lng
        self.dist = dist
        self.gpsElev = gpsElev
        self.mapElev = mapElev
        self.hr = hr

class Trackpoints:
    METERS_PER_MILE = 1609.344
    FEET_PER_METER = 3.28084
    elevWindow = 5

    def __init__(self, points):
        self.points = points

    def __len__(self):
        return len(self.points)

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

    def fromXML(cls, xmlTree, fname):
        times = xmlTree.findAll("Track/Trackpoint/Position/Time")
        lats = xmlTree.findAll("Track/Trackpoint/Position/LatitudeDegrees")
        lngs = xmlTree.findAll("Track/Trackpoint/Position/LongitudeDegrees")
        dists = xmlTree.findAll("Track/Trackpoint/DistanceMeters")
        altitudes = xmlTree.findAll("Track/Trackpoint/AltitudeMeters")
        hrs = xmlTree.findAll("Track/Trackpoint/HeartRateBpm/Value")
        points = []
        if len(lats) != len(lngs): 
            print>>sys.stderr, "ERROR in getting elev, num lats (", len(lats), ") != num longs (",len(lngs), ")"
        for i in range(0, min(len(lats), len(lngs))):
            points.append(Trackpoint(tm = times[i], lat = lats[i], lng = lngs[i], 
                                     dist = dists[i] / Trackpoints.METERS_PER_MILE, gpsElev = altitudes[i], 
                                     mapElev = 0, hr = hrs[i]))
        # check to see if there is already a file for elevations
        elevFname = fname + ".elev"
        if not os.path.exists(elevFname): 
            # no previous elevs file, fetch from google
            points = Trackpoints.getGoogleElevs(points)
            if len(points) > 0:
                # save the elevations to file
                f = open(elevFname, "w+")
                points.write(f)
                f.close()
        else:
            # previous elevs file, load up
            f = open(elevFname, "r")
            i = 0
            for line in f.readlines(): 
                tp = Trackpoint.fromFile(line)
                if tp.lat != points[i].lat or tp.lng != points[i].lng:
                    print>>sys.stderr, "Mismatch between points at index", i, "in file", elevFname
                    break
                points[i].mapElev = tp.mapElev
                i += 1
            f.close()
        return cls(points)
    fromXML = classmethod(fromXML)

    def write(self, outFile):
        for point in self.points: point.write(outFile)

    # this is taken from a google eg at 
    # http://gmaps-samples.googlecode.com/svn/trunk/elevation/python/ElevationChartCreator.py
    # The maximum length URL that can be submitted is 2048. Now a location takes 22 chars,
    # so with the base, the maximum number of points that can be submitted in one request 
    # is 90 
    # The usage limits constrain us to 2500 request per day or 25000 locations
    def getGoogleElevs(cls, points):
        if len(points) == 0: return []
        print>>sys.stdout, "Fetching elevations for", len(points), "points from google"
        ELEV_BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
        baseUrlLen = len(ELEV_BASE_URL) + len("?locations=") + len("&sensor=false")
        path = ""
        i = 0
        resultPoints = []
        for point in points:
            if path != "": path += "|"
            path += point.getUrlLatLng()
            i += 1
            url = ELEV_BASE_URL + '?' + urllib.urlencode({'locations': path, 'sensor': 'false'})
            # cannot have a longer url, so we make the request
            if len(url) > 2048 - 30 or i == len(points):
                # print url
                # print "sending url of length", (baseUrlLen + len(path)), len(url)
                response = simplejson.load(urllib.urlopen(url))
                # print response
                if response['status'] != "OK":
                    print>>sys.stderr, "Could not get elevs from Google:", response['status']
                    break
                for resultset in response['results']: 
                    lat = float(resultset['location']['lat'])
                    lng = float(resultset['location']['lng'])
                    elev = float(resultset['elevation'])
                    resultPoints.append(Trackpoint(lat = lat, lng = lng, mapElev = elev))
                path = ""
        if len(resultPoints) != len(points): 
            print>>sys.stderr, "Could not retrieve all", len(points), "points from google, only got", \
                len(resultPoints), "-- try again later"
        # now set the stored data
        for i in range(0, len(resultPoints)):
            if resultPoints[i].lat != points[i].lat:
                print>>sys.stderr, "Point mismatch at", i, ":"
                resultPoints[i].write(sys.stdout)
                points[i].write(sys.stdout)
                break
            else: points[i].mapElev = resultPoints[i].mapElev
        return points
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


