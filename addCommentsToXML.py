#!/usr/bin/python -u

import sys, optparse, string, os
from datetime import datetime
from lxml import etree

from pytracks.track import Track
from pytracks.courses import Courses

def main():
    cmdOptParser = optparse.OptionParser()
    (options, fnames) = cmdOptParser.parse_args()
    numFields = 13
    fname = "summary.dat"
    summaryTracks = {}
    elevs = {}
    knownDists = {}
    f = open(fname, "r")
    if f == None: return
    track = None
    num = 0
    METERS_PER_MILE = 1609.344
    FEET_PER_METER = 3.28084
    for line in f.readlines():
        if line.strip() == "": continue
        if line.lstrip()[0] == "#": 
            if track != None: track.comment += "\n" + line.rstrip()
            continue
        tokens = line.split(None, numFields)
        if len(tokens) == numFields: comment = ""
        else: comment = tokens[numFields].rstrip()
        track = Track(startTime = datetime.strptime(tokens[0] + tokens[1], "%Y-%m-%d%H:%M:%S"),
                      dist = float(tokens[2]), 
                      duration = float(tokens[4]), 
                      maxPace = float(tokens[5]),
                      maxHR = float(tokens[7]), 
                      avHR = float(tokens[8]),
                      trackpoints = None,
                      comment = comment)
        elevs[track.getStartTimeAsStr()] = float(tokens[9]) / FEET_PER_METER
        knownDists[track.getStartTimeAsStr()] = float(tokens[3]) * METERS_PER_MILE
        summaryTracks[track.getStartTimeAsStr()] = track
        num += 1
    print>>sys.stderr, "Read", num, "tracks from summary.dat"
    f.close()
#    for track in summaryTracks.values(): track.write(sys.stdout, False)
    for fname in fnames:
        (track, tree) = Track.fromXMLFile(fname)
        tree.root = "t:Activities/t:Activity"
        startTime = os.path.basename(fname).split(".")[0]
        if startTime in summaryTracks:
            print startTime, elevs[startTime], knownDists[startTime], track.comment
#            tree.delElem("", "Course")
            if elevs[startTime] > 0: 
                tree.addElem("", "KnownElevationMeters", elevs[startTime])
            if knownDists[startTime] > 0:
                 tree.addElem("", "KnownDistanceMeters", knownDists[startTime])
            # if summaryTracks[startTime].comment != "": 
            #     tree.addElem("", "Comment", summaryTracks[startTime].comment)
            tree.write(fname)

#            if courses[startTime] in Courses.data:
#                tree.addElem("", "Course", summaryTracks[startTime].course)
#                tree.write(fname)

if __name__ == "__main__": main()
