import numpy
import simplejson, urllib
from coord import Coord

METERS_PER_MILE = 1609.344
FEET_PER_METER = 3.28084

elevWindow = 5

class Coords:
    def __init__(self, points):
        global elevWindow
        self.points = points
        # smooth the elevations
        gpsSmoothed = []
        mapSmoothed = []
        for i in range(0, len(points) - elevWindow): 
            gpsSmoothed.append(numpy.average([p.gpsElev for p in self.points[i:i + elevWindow]]))
            mapSmoothed.append(numpy.average([p.mapElev for p in self.points[i:i + elevWindow]]))
        # compute elevation change
        self.gpsChange = 0
        self.mapChange = 0
        for i in range(0, len(gpsSmoothed) - 1):
            self.gpsChange += self.computeChange(gpsSmoothed[i + 1], gpsSmoothed[i])
            self.mapChange += self.computeChange(mapSmoothed[i + 1], mapSmoothed[i])
        self.gpsChange *= FEET_PER_METER
        self.mapChange *= FEET_PER_METER
        self.maxElev = 0
        self.minElev = 3000000
        for point in self.points: 
            if self.maxElev < point.mapElev: self.maxElev = point.mapElev
            if self.minElev > point.mapElev: self.minElev = point.mapElev

    def computeChange(self, first, second):
        change = first - second
        if change < 0: change = 0
        return change

    def fromTrackpoints(cls, lats, lngs, dists, altitudes):
        points = []
        if len(lats) != len(lngs): 
            print "ERROR in getting elev, num lats (", len(lats),\
                ") != num longs (",len(lngs), ")"
        for i in range(0, min(len(lats), len(lngs))):
            points.append(Coord(lats[i], lngs[i], dists[i] / METERS_PER_MILE, altitudes[i], 0))
        points = Coords.fromGoogle(points)
        return cls(points)
    fromTrackpoints = classmethod(fromTrackpoints)

    def fromFile(cls, fname):
        points = []
        f = open(fname, "r")
        for line in f.readlines(): points.append(Coord.fromFile(line))
        f.close()
        return cls(points)
    fromFile = classmethod(fromFile)

    def write(self, outFile):
        for point in self.points: point.write(outFile)

    # this is taken from a google eg at 
    # http://gmaps-samples.googlecode.com/svn/trunk/elevation/python/ElevationChartCreator.py
    # The maximum length URL that can be submitted is 2048. Now a location takes 22 chars,
    # so with the base, the maximum number of points that can be submitted in one request 
    # is 90 
    # The usage limits constrain us to 2500 request per day or 25000 locations
    def fromGoogle(cls, points):
        ELEV_BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
        baseUrlLen = len(ELEV_BASE_URL) + len("?locations=") + len("&sensor=false")
        path = ""
        i = 0
        resultPoints = []
        for point in points:
            if path != "": path += "|"
            path += point.getUrlLatLng()
            i += 1
            url = ELEV_BASE_URL + '?' + \
                urllib.urlencode({'locations': path, 'sensor': 'false'})
            # cannot have a longer url, so we make the request
            if len(url) > 2048 - 30 or i == len(points):
                # print url
                # print "sending url of length", (baseUrlLen + len(path)), len(url)
                response = simplejson.load(urllib.urlopen(url))
                # print response
                if response['status'] != "OK":
                    print "Could not get elevs from Google: ", response['status']
                    break
                for resultset in response['results']: 
                    lat = float(resultset['location']['lat'])
                    lng = float(resultset['location']['lng'])
                    elev = float(resultset['elevation'])
                    resultPoints.append(Coord(lat = lat, lng = lng, mapElev = elev))
                path = ""
        print "Found", i, "elevs for", len(points), "points"
        # now set the stored data
        for i in range(0, len(resultPoints)):
            if resultPoints[i].lat != points[i].lat:
                print "Point mismatch at", i, ":"
                resultPoints[i].write(sys.stdout)
                points[i].write(sys.stdout)
                break
            else: points[i].mapElev = resultPoints[i].mapElev
        return points
    fromGoogle = classmethod(fromGoogle)

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
        for point in self.points: elevs.append(point.mapElev)
        return elevs
    
    def getLats(self):
        lats = []
        for point in self.points: lats.append(point.lat)
        return lats
    
    def getLngs(self):
        lngs = []
        for point in self.points: lngs.append(point.lng)
        return lngs
