#!/usr/bin/python -u 

import argparse, string, os, sys
import gtk, datetime
import pytracks
from pytracks.tracks import Tracks
from pytracks.track import Track
from pytracks.trackpoints import Trackpoints

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
    cmdOptParser.add_argument("-w", action = "store", type = int, dest = "elevWindow", 
                              default = 5, help = "Window size for smoothing elevations")
    cmdOptParser.add_argument("-p", action = "store", type = str, dest = "printTracks", 
                              default = "", 
                              help = "Print track for date (YYYY-MM-DD-HHMMSS), " +\
                                  "'all' for all tracks")
    cmdOptParser.add_argument("-s", action = "store", type = str, dest = "printSimilar", 
                              default = "", 
                              help = "Print all tracks similar to date (YYYY-MM-DD-HHMMSS)")
    cmdOptParser.add_argument("-t", action = "store_true", dest = "showTerrain", 
                              default = False, help = "Show terrain on map instead of aerial photo")
    cmdOptParser.add_argument("-z", action = "store", type = str, dest = "tz", 
                              default = "US/Pacific", 
                              help = "Set time zone for xml conversion")
    cmdOptParser.add_argument("fnames", metavar='N', type = str, nargs = '*',
                              help="a list of xml files containing TCX data")
    options = cmdOptParser.parse_args()

    Trackpoints.elevWindow = options.elevWindow
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
        from pytracks.maptracks import MapTracks
        from pytracks.plottracks import PlotTracks
        try:
            track = tracks[options.plotMap]
        except:
            print "Cannot find track for", options.plotMap
            sys.exit(0)
        if len(track) == 0: 
            print "Track", options.plotMap, "has no trackpoints"
            sys.exit(0)
        title = "Track %s, %.1f m, %.0f ft" % (options.plotMap, track.dist, track.getElevChange())
        mapTracks = MapTracks(track, title, color = "red", width = 800, height = 600, 
                              showTerrain = options.showTerrain)
        mapTracks.show_all()
        # Now here we plot elev profile, pace profile, hr profile, comparison to other similar
        # runs, etc
        plotTracks = PlotTracks(track, title, color = "red", width = 700, height = 500)
        plotTracks.show_all()

        gtk.main()


if __name__ == "__main__": main()
