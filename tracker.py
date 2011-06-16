#!/usr/bin/python -u 

import argparse, string, os, sys
import gtk, datetime
import pytracks
from pytracks.tracks import Tracks
from pytracks.track import Track
from pytracks.trackpoints import Trackpoints
from pytracks.maptracks import MapTracks
from pytracks.plotxy import PlotXY

def main():
    # get the command line options
    cmdOptParser = argparse.ArgumentParser(description = "Analyze Garmin GPS data",
                                           formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cmdOptParser.add_argument("-f", action = "store", type = str, dest = "tracksFname", 
                              default = "tracks.pck", 
                              help = "Name of tracks file containing pickle data")
    cmdOptParser.add_argument("-m", action = "store", type = str, dest = "plotMap", 
                              default = "", 
                              help = "Show track on map for date (YYYY-MM-DD)")
    cmdOptParser.add_argument("-e", action = "store", type = int, dest = "elevWindow", 
                              default = 2, help = "Window size for smoothing elevations")
    cmdOptParser.add_argument("-r", action = "store", type = int, dest = "hrWindow", 
                              default = 20, help = "Window size for smoothing heart rates")
    cmdOptParser.add_argument("-c", action = "store", type = int, dest = "paceWindow", 
                              default = 20, help = "Window size for smoothing paces")
    cmdOptParser.add_argument("-p", action = "store", type = str, dest = "printTracks", 
                              default = "", 
                              help = "Print tracks for dates of form (YYYY-MM-DD-HHMMSS) or " +\
                                  "a substritng of that, e.g. 2011-04")
    cmdOptParser.add_argument("-s", action = "store", type = str, dest = "printSimilar", 
                              default = "", 
                              help = "Print all tracks similar to date (YYYY-MM-DD-HHMMSS)")
    cmdOptParser.add_argument("-t", action = "store_true", dest = "showTerrain", 
                              default = False, help = "Show terrain on map instead of aerial photo")
    cmdOptParser.add_argument("-z", action = "store", type = str, dest = "tz", 
                              default = "US/Pacific", 
                              help = "Set time zone for xml conversion")
    cmdOptParser.add_argument("-n", action = "store_true", dest = "monthlyStats", 
                              default = False, help = "Plot monthly stats")
    cmdOptParser.add_argument("fnames", metavar='N', type = str, nargs = '*',
                              help="a list of xml files containing TCX data")
    options = cmdOptParser.parse_args()

    tracks = Tracks()
    tracks.load(options.tracksFname)
    # now update with any new data
    tracks.updateFromXML(options.fnames, options.tz)
    if len(tracks) == 0: 
        print>>sys.stderr, "No tracks found"
        sys.exit(0)
    tracks.save(options.tracksFname)
    if options.printTracks != "": tracks.write(sys.stdout, options.printTracks)
    if options.plotMap != "": 
        try:
            track = tracks[options.plotMap]
        except:
            print "Cannot find track for", options.plotMap
            sys.exit(0)
        if len(track) == 0: 
            print "Track", options.plotMap, "has no trackpoints"
            sys.exit(0)
        title = "Track %s, %.1f m, %.0f ft" % (options.plotMap, track.dist, 
                                               track.getElevChange(options.elevWindow))
        mapTracks = MapTracks(track, "Map of " + title, color = "red", width = 800, height = 600, 
                              showTerrain = options.showTerrain)
        mapTracks.show_all()
        # Now here we plot elev profile, pace profile, hr profile, comparison to other similar
        # runs, etc
        plotElevHrs = PlotXY(track.trackpoints.dists, track.trackpoints.getElevs(),
                                 "Distance (miles)", "Elevation (ft)",
                                 "Elevation and heart rate for " + title, color = "red", 
                                 width = 700, height = 300, 
                                 smoothingWindow = options.elevWindow)
        plotElevHrs.addSecond(track.trackpoints.dists, track.trackpoints.hrs, "Heart Rate (bpm)",
                              "green", smoothingWindow = options.hrWindow)
        plotElevHrs.show_all()
        plotElevPace = PlotXY(track.trackpoints.dists, track.trackpoints.getElevs(),
                                  "Distance (miles)", "Elevation (ft)",
                                  "Elevation and pace for " + title, color = "red", 
                                  width = 700, height = 300, 
                                  smoothingWindow = options.elevWindow)
        plotElevPace.addSecond(track.trackpoints.dists, track.trackpoints.getPaces(), 
                               "Pace (mile / min)", "green", smoothingWindow = options.paceWindow)
        plotElevPace.show_all()
        gtk.main()
    if options.monthlyStats:
        (months, dists, paces) = tracks.getMonthlyStats()
        plotMonthly = PlotXY(months, dists, "Date", "Distance (miles)",
                             "Monthly distance and pace", color = "red", width = 700, height = 300)
        plotMonthly.addSecond(months, paces, "Pace (mile / min)", "green")
        plotMonthly.show_all()
        gtk.main()
        

if __name__ == "__main__": main()
