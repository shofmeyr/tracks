#!/usr/bin/python -u

import sys, datetime
from datetime import datetime 
from pytracks.track import Track

METERS_PER_MILE = 1609.344

def main():
    fname = "summary.dat"
    tracks = {}
    f = open(fname, "r")
    if f == None: return
    found = None
    num = 0
    numFields = 13
    for line in f.readlines():
        if line.strip() == "": continue
        if line.lstrip()[0] == "#": 
            if found != None: found.comment += "\n" + line.rstrip()
            continue
        tokens = line.split(None, numFields)
        if len(tokens) == numFields: comment = ""
        else: comment = tokens[numFields].rstrip()
        savedTrack = Track(startTime = datetime.strptime(tokens[0] + tokens[1], "%Y-%m-%d%H:%M:%S"),
                      dist = float(tokens[2]), 
                      duration = float(tokens[4]), 
                      maxPace = float(tokens[5]),
                      maxHR = float(tokens[7]), 
                      avHR = float(tokens[8]),
                      trackpoints = None,
                      course = tokens[12],
                      comment = comment)
        found = None
        for track in tracks.values():
            if savedTrack.startTime == track.startTime: 
                track.course = savedTrack.course
                track.comment = savedTrack.comment
                found = track
                num += 1
                break
        if found == None: 
            tracks[savedTrack.getStartTimeAsStr()] = savedTrack
            num += 1
    print>>sys.stderr, "Loaded additional data for", num, "tracks from \"" + fname + "\""
    f.close()
    for track in sorted(tracks.values(), key=lambda track: track.startTime):
        xmlFname = track.getStartTimeAsStr() + ".tcx"
        idTime = track.startTime.strftime("%Y-%m-%dT%H:%M:%SZ")
        f = open(xmlFname, "w+")
        print>>f, "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?>\n",\
            "<TrainingCenterDatabase xmlns=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2\"",\
            "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"",\
            "xsi:schemaLocation=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",\
            "http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd\">"
        print>>f, "  <Activities>"
        print>>f, "    <Activity Sport=\"Running\">"
        print>>f, "      <Id>" + idTime + "</Id>"
        print>>f, "      <Lap StartTime=\"" + idTime + "\">"
        print>>f, "        <TotalTimeSeconds>" + str(track.duration * 60.0) + "</TotalTimeSeconds>"
        print>>f, "        <DistanceMeters>" + str(track.dist * METERS_PER_MILE) + "</DistanceMeters>"
# FIXME: if you include maxPace, you need to convert from minutes per mile to km/hr
#        print>>f, "        <MaximumSpeed>" + str(track.maxPace) + "</MaximumSpeed>
#        print>>f, "        <Calories>0</Calories>"
        print>>f, "        <AverageHeartRateBpm xsi:type=\"HeartRateInBeatsPerMinute_t\">"
        print>>f, "          <Value>" + str(track.avHR) + "</Value>"
        print>>f, "        </AverageHeartRateBpm>"
        print>>f, "        <MaximumHeartRateBpm xsi:type=\"HeartRateInBeatsPerMinute_t\">"
        print>>f, "          <Value>" + str(track.maxHR) + "</Value>"
        print>>f, "        </MaximumHeartRateBpm>"
        print>>f, "        <Intensity>Active</Intensity>"
        print>>f, "        <TriggerMethod>Manual</TriggerMethod>"
        print>>f, "      </Lap>"
        print>>f, "      <Creator xsi:type=\"Device_t\">"
        print>>f, "        <Name>green</Name>"
        print>>f, "        <UnitId>3439781637</UnitId>"
        print>>f, "        <ProductID>717</ProductID>"
        print>>f, "        <Version>"
        print>>f, "          <VersionMajor>2</VersionMajor>"
        print>>f, "          <VersionMinor>50</VersionMinor>"
        print>>f, "          <BuildMajor>0</BuildMajor>"
        print>>f, "          <BuildMinor>0</BuildMinor>"
        print>>f, "        </Version>"
        print>>f, "      </Creator>"
        print>>f, "    </Activity>"
        print>>f, "  </Activities>"
        print>>f, ""
        print>>f, "  <Author xsi:type=\"Application_t\">"
        print>>f, "    <Name>Garmin ANT Agent(tm)</Name>"
        print>>f, "    <Build>"
        print>>f, "      <Version>"
        print>>f, "        <VersionMajor>2</VersionMajor>"
        print>>f, "        <VersionMinor>2</VersionMinor>"
        print>>f, "        <BuildMajor>7</BuildMajor>"
        print>>f, "        <BuildMinor>0</BuildMinor>"
        print>>f, "      </Version>"
        print>>f, "      <Type>Release</Type>"
        print>>f, "      <Time>Jul 30 2009, 17:42:56</Time>"
        print>>f, "      <Builder>sqa</Builder>"
        print>>f, "    </Build>"
        print>>f, "    <LangID>EN</LangID>"
        print>>f, "    <PartNumber>006-A0214-00</PartNumber>"
        print>>f, "  </Author>"
        print>>f, "</TrainingCenterDatabase>"
        f.close()

if __name__ == "__main__": main()
