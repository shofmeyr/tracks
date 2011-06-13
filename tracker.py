#!/usr/bin/python -u 

import optparse, string, os, sys
import gtk, datetime
import pytracks
from pytracks.tracks import Tracks
from pytracks.track import Track
from pytracks.trackpoints import Trackpoints

def main():
    # get the command line options
    cmdOptParser = optparse.OptionParser()
    cmdOptParser.add_option("-f", action = "store", type = "string", dest = "tracksFname", 
                            default = "tracks.pck", 
                            help = "Name of tracks file containing pickle data")
    cmdOptParser.add_option("-m", action = "store", type = "string", dest = "plotMap", 
                            default = "", 
                            help = "Show track on map for date (YYYY-MM-DD)")
    cmdOptParser.add_option("-w", action = "store", type = "int", dest = "elevWindow", 
                            default = 5, help = "Window size for smoothing elevations")
    cmdOptParser.add_option("-p", action = "store", type = "string", dest = "printTracks", 
                            default = "", 
                            help = "Print track for date (YYYY-MM-DD), or 'all' for all tracks")
    cmdOptParser.add_option("-s", action = "store", type = "string", dest = "printSimilarTracks", 
                            default = "", 
                            help = "Print all tracks similar to date (YYYY-MM-DD)")
    cmdOptParser.add_option("-t", action = "store_true", dest = "showTerrain", 
                            default = False, help = "Show terrain on map instead of aerial photo")
    cmdOptParser.add_option("-z", action = "store", type = "string", dest = "tz", 
                            default = "", help = "Set time zone for all points converted from xml")
    (options, fnames) = cmdOptParser.parse_args()
    Trackpoints.elevWindow = options.elevWindow
    tracks = Tracks()
    tracks.load(options.tracksFname)
    # now update with any new data
    tracks.updateFromXML(fnames, options.tz)
    if len(tracks) == 0: 
        print>>sys.stderr, "No tracks found"
        sys.exit(0)
    tracks.save(options.tracksFname)
    if options.printTracks != "": tracks.write(sys.stdout, options.printTracks, options.useGps)
    if options.plotMap != "": 
        from pytracks.maptracks import MapTracks
        colors = ["red", "green", "blue", "yellow", "black", "cyan", "magenta"]
        mapTracks = MapTracks(options.showTerrain)
        win = gtk.Window()
        win.connect("destroy", lambda x: gtk.main_quit())
        win.set_default_size(600, 400)
        vbox = gtk.VBox()
        win.add(vbox)
        mapTracks.set_title(title)
        mapTracks.show_all()
        # Now here we plot elev profile, pace profile, hr profile, comparison to other similar
        # runs, etc
#        plotTracks = PlotTracks()
        gtk.main()


if __name__ == "__main__": main()
