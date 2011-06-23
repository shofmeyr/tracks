#!/usr/bin/python -u

import sys, optparse, string, os, pytz
from datetime import datetime
from lxml import etree

from pytracks.track import Track
#from pytracks.courses import Courses

def main():
    cmdOptParser = optparse.OptionParser()
    (options, fnames) = cmdOptParser.parse_args()
    numFields = 13
    fname = "summary.dat"
    elevs = {}
    knownDists = {}
    comments = {}
    courses = {}
    f = open(fname, "r")
    if f == None: return
    num = 0
    METERS_PER_MILE = 1609.344
    FEET_PER_METER = 3.28084
    for line in f.readlines():
        if line.strip() == "": continue
        if line.lstrip()[0] == "#": 
            if num > 0: comments[startTime] += "\n" + line.rstrip()
            continue
        tokens = line.split(None, numFields)
        if len(tokens) == numFields: comment = ""
        else: comment = tokens[numFields].rstrip()
        startTime = tokens[0]
        dist = float(tokens[3]) * METERS_PER_MILE
        if dist > 0: knownDists[startTime] = dist
        elev = float(tokens[9]) / FEET_PER_METER
        if elev > 0: elevs[startTime] = elev
        if tokens[12] != "": courses[startTime] = tokens[12]
        comments[startTime] = comment
        num += 1
    print>>sys.stderr, "Read", num, "tracks from summary.dat"
    f.close()
#    for track in summaryTracks.values(): track.write(sys.stdout, False)
    for fname in fnames:
        (track, tree) = Track.from_xml_file(fname, "US/Pacific")
        if tree is None: continue
        tree.root = "t:Activities/t:Activity"
        startTime = track.start_time.strftime("%Y-%m-%d")
        if not (startTime in knownDists or startTime in elevs or startTime in comments): 
            print startTime, "not found"
        else:
            print startTime, 
            if startTime in elevs:
                print "elev", elevs[startTime] * FEET_PER_METER, 
                if elevs[startTime] > 0: tree.add_elem("", "KnownElevationMeters", elevs[startTime])
            if startTime in knownDists:
                print "dist", knownDists[startTime] / METERS_PER_MILE, 
                if knownDists[startTime] > 0: tree.add_elem("", "KnownDistanceMeters", knownDists[startTime])
            if startTime in comments:
                print "comment", comments[startTime],
                if comments[startTime] != "": tree.add_elem("", "Comment", comments[startTime])
            if startTime in courses:
                print "course", courses[startTime],
                tree.add_elem("", "Course", courses[startTime])
            print ""
            tree.write(track.start_time.strftime("%Y-%m-%d-%H%M%S.tcx"))

if __name__ == "__main__": main()
