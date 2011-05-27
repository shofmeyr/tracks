#!/usr/bin/python -u 

from datetime import datetime as dt
from matplotlib.figure import Figure
import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
import optparse, string, os, sys
import matplotlib.pyplot as pyplot
import gtk
import pytracks
from pytracks.courses import Courses
from pytracks.tracks import Tracks
from pytracks.mapviewer import MapViewer
from pytracks.track import Track
from pytracks.trackpoints import Trackpoints

def main():
    # get the command line options
    cmdOptParser = optparse.OptionParser()
    cmdOptParser.add_option("-f", action = "store", type = "string", dest = "tracksFname", 
                            default = "tracks.pck", help = "Name of tracks file containing pickle data")
    cmdOptParser.add_option("-c", action = "store", type = "string", dest = "coursesFname", 
                            default = "", help = "Name of courses data file")
    cmdOptParser.add_option("-m", action = "store", type = "string", dest = "plotMap", 
                            default = "", help = "Print track/s for course or date (YYYY-MM-DD), or 'all' for all tracks")
    cmdOptParser.add_option("-w", action = "store", type = "int", dest = "elevWindow", 
                            default = 5, help = "Window size for smoothing elevations")
    cmdOptParser.add_option("-p", action = "store", type = "string", dest = "printTracks", 
                            default = "", help = "Print track/s for course or date (YYYY-MM-DD), or 'all' for all tracks")
    cmdOptParser.add_option("-g", action = "store_true", dest = "useGps", 
                            default = False, help = "Use the GPS distance and elev instead of the course values")
    cmdOptParser.add_option("-t", action = "store_true", dest = "showTerrain", 
                            default = False, help = "Show terrain on map instead of aerial photo")
    cmdOptParser.add_option("--fromtext", action = "store", type = "string", dest = "textSummaryFname", 
                            default = "", help = "Read additional tracks data from named text file")
    (options, fnames) = cmdOptParser.parse_args()
    Trackpoints.elevWindow = options.elevWindow
    # get the course data
    Courses.load(options.coursesFname)
    tracks = Tracks()
    tracks.load(options.tracksFname, options.textSummaryFname)
    # now update with any new data
    tracks.updateFromXML(fnames)
    if len(tracks) == 0: 
        print>>sys.stderr, "No tracks found"
        sys.exit(0)
    tracks.save(options.tracksFname)

    if options.printTracks != "": tracks.write(sys.stdout, options.printTracks, options.useGps)
    if options.plotMap != "":
        trackDate = None
        try: 
            trackDate = Track.getTimeFromFname(options.plotMap + ".tcx")
            title = "Track " + options.plotMap
        except ValueError: 
            pass
        if trackDate == None:
            try:
                title = "Course " + options.plotMap + ":  %.0f miles" % Courses.data[options.plotMap].dist + \
                    " %.0f feet" % Courses.data[options.plotMap].elevChange
            except KeyError:
                print>>sys.stderr, "*** ERROR: course", options.plotMap, "not found ***"
                sys.exit(0)
        mapViewer = MapViewer(options.showTerrain)
        colors = ["red", "green", "blue", "yellow", "black", "cyan", "magenta"]
        win = gtk.Window()
        win.connect("destroy", lambda x: gtk.main_quit())
        win.set_default_size(600, 400)
        vbox = gtk.VBox()
        win.add(vbox)
        fig = Figure()
        ax = fig.add_subplot(111)
        minElev = 300000
        maxElev = 0
        maxDist = 0
        i = 0
        found = False
        for track in tracks.getSortedTracks():
            if len(track) > 0:
                if (trackDate != None and track.startTime == trackDate) or track.course == options.plotMap:
                    if not mapViewer.addTrack(track.trackpoints.getLats(), track.trackpoints.getLngs(), color = colors[i]):
                        print>>sys.stderr, "Track", track.startTime, "is empty"
                    else:
                        (gpsElevChange, mapElevChange) = track.trackpoints.getElevChanges()
                        ax.plot(track.trackpoints.getDists(), track.trackpoints.getMapElevs(), 
                                label = track.getDate() + " (" + ("%.0f" % mapElevChange) + ")", color = colors[i])
                    (trackMinElev, trackMaxElev) = track.trackpoints.getMinMaxElevs(options.useGps)
                    if maxElev < trackMaxElev: maxElev = trackMaxElev
                    if minElev > trackMinElev: minElev = trackMinElev
                    if maxDist < track.dist: maxDist = track.dist
                    found = True
                    i += 1
                    if i == len(colors): i = 0
                    if trackDate != None: 
                        title += ":  %.0f miles" % track.dist + " %.0f feet" % track.getElevChange(options.useGps)
                        break
        if not found:
            if trackDate != None: print>>sys.stderr, "*** ERROR: Track", options.plotMap, "not found ***"
            else: print>>sys.stderr, "*** ERROR: course", options.plotMap, "not found ***"
            sys.exit(0)
        ax.legend(loc = "lower right", prop = font_manager.FontProperties(size = "x-small"))
        ax.axis([0, maxDist, minElev - 200, maxElev])
        ax.get_axes().set_xlabel("Distance (miles)")
        ax.get_axes().set_ylabel("Elevation (ft)")
        ax.get_axes().grid()
        canvas = FigureCanvas(fig)  
        vbox.pack_start(canvas)
        toolbar = NavigationToolbar(canvas, win)
        vbox.pack_start(toolbar, False, False)
        mapViewer.set_title(title)
        mapViewer.show_all()
        win.set_title("Elevation profile, " + title)
        win.show_all()
        gtk.main()


if __name__ == "__main__": main()
