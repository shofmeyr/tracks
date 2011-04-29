#!/usr/bin/python -u 

from datetime import datetime as dt
from matplotlib.figure import Figure
import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
import optparse, string, os, sys
import matplotlib.pyplot as pyplot
import gtk
import pyruns
from pyruns.courses import Courses
from pyruns.runs import Runs
from pyruns.mapviewer import MapViewer
from pyruns.run import Run
from pyruns.coords import Coords

def main():
    # get the command line options
    cmdOptParser = optparse.OptionParser()
    cmdOptParser.add_option("-f", action = "store", type = "string", dest = "runsFname", 
                            default = "runs", help = "Name of runs file containing pickle data")
    cmdOptParser.add_option("-c", action = "store", type = "string", dest = "coursesFname", 
                            default = "courses.dat", help = "Name of courses data file")
    cmdOptParser.add_option("--map", action = "store", type = "string", dest = "plotMap", 
                            default = "", help = "Name of course to plot (all runs) or date (YYYY-MM-DD) of course to plot")
    cmdOptParser.add_option("--googlemap", action = "store", type = "string", dest = "plotGoogleMap", 
                            default = "", help = "Plots the run given by the date (YYYY-MM-DD) on a google terrain map")
    cmdOptParser.add_option("-w", action = "store", type = "int", dest = "elevWindow", 
                            default = 5, help = "Window size for smoothing elevations")
    cmdOptParser.add_option("-p", action = "store", type = "string", dest = "printRuns", default = "", 
                            help = "Print run/s for course or date (YYYY-MM-DD), or 'all' for all runs")
    cmdOptParser.add_option("-g", action = "store_true", dest = "useGps", 
                            default = False, help = "Use the GPS distance and elev instead of the course values")
    (options, fnames) = cmdOptParser.parse_args()
    Coords.elevWindow = options.elevWindow
    # get the course data
    Courses.load(options.coursesFname)
    runs = Runs()
    runs.load(options.runsFname)
    # now update with any new data
    runs.updateFromXML(fnames)
    runs.save(options.runsFname)
    # plot efficiency vs elev rate
    #pyplot.plot(runs.getEfficiencies(), runs.getElevRates(), "x")
    #pyplot.show()
    if options.printRuns != "": runs.write(sys.stdout, options.printRuns, options.useGps)
    if options.plotMap != "":
        runDate = None
        try: 
            runDate = Run.getTimeFromFname(options.plotMap + ".tcx")
            title = "Run " + options.plotMap
        except ValueError: 
            pass
        if runDate == None:
            try:
                title = "Course " + options.plotMap + ":  %.0f miles" % Courses.data[options.plotMap].dist + \
                    " %.0f feet" % Courses.data[options.plotMap].elevChange
            except KeyError:
                print "*** ERROR: course", options.plotMap, "not found ***"
                sys.exit(0)
        mapViewer = MapViewer()
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
        for run in runs.getSortedRuns():
            if run.coords != None: 
                if (runDate != None and run.startTime == runDate) or run.course == options.plotMap:
                    if not mapViewer.addTrack(run.coords.getLats(), run.coords.getLngs(), color = colors[i]):
                        print "Track", run.startTime, "is empty"
                    else:
                        (gpsElevChange, mapElevChange) = run.coords.getElevChanges()
                        ax.plot(run.coords.getDists(), run.coords.getMapElevs(), 
                                label = run.getDate() + " (" + ("%.0f" % mapElevChange) + ")", color = colors[i])
                    (runMinElev, runMaxElev) = run.coords.getMinMaxElevs(options.useGps)
                    if maxElev < runMaxElev: maxElev = runMaxElev
                    if minElev > runMinElev: minElev = runMinElev
                    if maxDist < run.dist: maxDist = run.dist
                    found = True
                    i += 1
                    if i == len(colors): i = 0
                    if runDate != None: 
                        title += ":  %.0f miles" % run.dist + " %.0f feet" % run.getElevChange(options.useGps)
                        break
        if not found:
            if runDate != None: print "*** ERROR: Run", options.plotMap, "not found ***"
            else: print "*** ERROR: course", options.plotMap, "not found ***"
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

    elif options.plotGoogleMap != "":
        pyplot.axes([0,0,1,1], frameon=False).set_axis_off()
        found = False
        for run in runs.getSortedRuns():
            if run.coords != None: 
                if run.getStartTimeAsStr() == options.plotGoogleMap:
                    image = run.getGoogleImage()
                    pyplot.imshow(image)
                    pyplot.show()
                    found = True
                    break
        if not found:
            print "*** ERROR: course", options.plotMap, "not found ***"
            sys.exit(0)

if __name__ == "__main__": main()
