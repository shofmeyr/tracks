import numpy
import sys
import simplejson
import urllib
import os
import datetime

class Trackpoints:
    METERS_PER_MILE = 1609.344
    FEET_PER_METER = 3.28084

    def __init__(self):
        self.times = []
        self.lats = []
        self.lngs = []
        self.dists = []
        self.gps_elevs = []
        self.map_elevs = []
        self.hrs = []
        self.length = 0

    def __len__(self):
        return self.length

    def get_elev_change(self, smooth_window):
        # smooth the elevations
        if smooth_window == 0: 
            if len(self.map_elevs) > 0: smoothed_elevs = self.map_elevs
            else: smoothed_elevs = self.gps_elevs
        else:
            smoothed_elevs = []
            for i in range(smooth_window, len(self) - smooth_window): 
                if len(self.map_elevs) > 0: elevs = self.map_elevs
                else: elevs = self.gps_elevs
                smoothed_elevs.append(numpy.average(elevs[i - smooth_window:i + smooth_window]))
        # compute elevation change
        tot_change = 0
        for i in range(0, len(smoothed_elevs) - 1):
            change = smoothed_elevs[i + 1] - smoothed_elevs[i]
            if change < 0: change = 0
            tot_change += change
        tot_change *= Trackpoints.FEET_PER_METER
        return tot_change

    def get_min_max_elevs(self):
        if len(self.map_elevs) > 0: elevs = self.map_elevs
        else: elevs = self.gps_elevs
        min_elev = min(elevs)
        max_elev = max(elevs)
        return (min_elev * Trackpoints.FEET_PER_METER, max_elev * Trackpoints.FEET_PER_METER)

    def get_elevs(self):
        if len(self.map_elevs) > 0: elevs = self.map_elevs
        else: elevs = self.gps_elevs
        return [e * Trackpoints.FEET_PER_METER for e in elevs]

    def get_paces(self):
        paces = []
        first_i = 0
        pace = 0
        for i in range(0, min(len(self.times), len(self.dists))):
            dist_diff = self.dists[i] - self.dists[first_i]
            if dist_diff < 0.05: 
                paces.append(pace)
                continue
            try:
                t1 = datetime.datetime.strptime(self.times[first_i], "%Y-%m-%dT%H:%M:%SZ") 
                t2 = datetime.datetime.strptime(self.times[i], "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                t1 = datetime.datetime.strptime(self.times[first_i], "%Y-%m-%dT%H:%M:%S.000Z") 
                t2 = datetime.datetime.strptime(self.times[i], "%Y-%m-%dT%H:%M:%S.000Z")
            td = t2 - t1
            tot_mins = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 / 60.0
            pace = tot_mins / dist_diff
            if pace < 4: pace = 4
            if pace > 25: pace = 25
            paces.append(pace)
            first_i = i
        return paces

    def load_from_xml(self, tree, fname):
        root = "t:Track/t:Trackpoint/"
        self.times = tree.find_all(root + "t:Time", False)
        self.lats = tree.find_all(root + "t:Position/t:LatitudeDegrees")
        self.lngs = tree.find_all(root + "t:Position/t:LongitudeDegrees")
        self.dists = [d / Trackpoints.METERS_PER_MILE 
                      for d in tree.find_all(root + "t:DistanceMeters")]
        self.gps_elevs = tree.find_all(root + "t:AltitudeMeters")
        self.hrs = tree.find_all(root + "t:HeartRateBpm/t:Value")
        self.map_elevs = tree.find_all(root + "t:MapAltitudeMeters")
        if not (len(self.times) >= len(self.lats) == len(self.lngs) == len(self.dists) == 
                len(self.gps_elevs) == len(self.hrs)): 
            print>>sys.stderr, "Missing points in xml file", fname, ":",\
                "times", len(self.times), "lats", len(self.lats), "lngs",\
                len(self.lngs), "dists", len(self.dists),\
                "altitudes", len(self.gps_elevs), "hrs", len(self.hrs)
        self.length = min([len(self.times), len(self.lats), len(self.lngs), len(self.dists), 
                           len(self.gps_elevs), len(self.hrs)])
        if len(self.map_elevs) == 0 and len(self.gps_elevs) > 0:
            # no previous elevations, fetch from google
            if not os.path.exists(fname + ".elev"): 
                self.map_elevs = Trackpoints._get_google_elevs(self.lats, self.lngs)
#            else: map_elevs = Trackpoints._read_elevs_file(fname + ".elev")
            if len(self.map_elevs) > 0:
                # add the elevs to the xmltree
                print>>sys.stderr, "Adding", len(self.map_elevs), "map elevations to", fname
                tree.add_elems("t:Track/t:Trackpoint", "MapAltitudeMeters", 
                               self.map_elevs, "AltitudeMeters")

    @classmethod
    def _read_elevs_file(cls, elev_fname):
        f = open(elev_fname, "r")
        elevs = []
        for line in f.readlines(): 
            tokens = line.lstrip().rstrip().split()
            lat = float(tokens[0])
            lng = float(tokens[1])
            map_elev = float(tokens[4])
            elevs.append(map_elev)
        f.close()
        return elevs

    def write(self, out_file):
        for i in range(0, len(self)):
            print>>out_file, self.lats[i], self.lngs[i], self.dists[i], self.gps_elevs[i], \
                self.map_elevs[i], self.hrs[i]

    # this is taken from a google eg at 
    # http://gmaps-samples.googlecode.com/svn/trunk/elevation/python/ElevationChartCreator.py
    # The maximum length URL that can be submitted is 2048. Now a location takes 22 chars,
    # so with the base, the maximum number of points that can be submitted in one request 
    # is 90 
    # The usage limits constrain us to 2500 request per day or 25000 locations
    @classmethod
    def _get_google_elevs(cls, lats, lngs):
        if len(lats) == 0: return []
        print>>sys.stderr, "Fetching elevations for", len(lats), "points from google"
        ELEV_BASE_URL = 'http://maps.google.com/maps/api/elevation/json'
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
            print>>sys.stderr, "Could not retrieve all", len(lats), \
                "points from google, only got", len(elevs), "-- try again later"
            return []
        return elevs


