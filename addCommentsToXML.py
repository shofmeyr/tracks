#!/usr/bin/python -u

import sys, optparse
from datetime import datetime
from lxml import etree

from pytracks.track import Track

def main():
    cmdOptParser = optparse.OptionParser()
    (options, fnames) = cmdOptParser.parse_args()
    numFields = 13
    fname = "summary.dat"
    summaryTracks = {}
    f = open(fname, "r")
    if f == None: return
    track = None
    num = 0
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
                      course = tokens[12],
                      comment = comment)
        summaryTracks[track.getStartTimeAsStr()] = track
        num += 1
    print>>sys.stderr, "Read", num, "tracks from summary.dat"
    f.close()
#    for track in summaryTracks.values(): track.write(sys.stdout, False)
    # read from courses.dat into courses dictionary
    Courses.load("courses.dat")

    for fname in fnames:
        (track, tree) = Track.fromXMLFile(fname)
        tree.root = "t:Activities/t:Activity"
        startTime = track.getStartTimeAsStr()
        if startTime in summaryTracks:
#            if summaryTracks[startTime].comment != "": 
#                tree.addElem("", "Comment", summaryTracks[startTime].comment)
            if summaryTracks[startTime].course != "": 
#                tree.addElem("", "Course", summaryTracks[startTime].course)
                tree.addElem("", "MaxElevationMeters", 
                             courses[summaryTracks[startTime].course].elevGain)
            tree.write(fname)

if __name__ == "__main__": main()
