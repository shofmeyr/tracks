#!/usr/bin/python -u 


class Coord:
    def __init__(self, lat, lng, dist = 0, gpsElev = 0, mapElev = 0):
        self.lat = lat
        self.lng = lng
        self.dist = dist
        self.gpsElev = gpsElev
        self.mapElev = mapElev

    def fromFile(cls, line):
        tokens = line.split()
        return cls(float(tokens[0]), float(tokens[1]), float(tokens[2]), float(tokens[3]),
                   float(tokens[4]))
    fromFile = classmethod(fromFile)

    def getUrlLatLng(self):
        return str(self.lat) + "," + str(self.lng)

    def write(self, outFile):
        print >> outFile, self.lat, self.lng, "%6.3f" % self.dist, \
            "%6.0f" % round(self.gpsElev), "%6.0f" % round(self.mapElev)
        
    def __setattr__(self, mapElev, val): 
        self.__dict__[mapElev] = val


