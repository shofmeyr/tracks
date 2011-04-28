#!/usr/bin/python -u 

from datetime import datetime as dt
from matplotlib.figure import Figure
import matplotlib.font_manager as font_manager
from numpy import arange, sin, pi

# uncomment to select /GTK/GTKAgg/GTKCairo
#from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas

# or NavigationToolbar for classic
#from matplotlib.backends.backend_gtk import NavigationToolbar2GTK as NavigationToolbar
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar


import optparse, string, os, sys
import matplotlib.pyplot as pyplot
import gtk.gdk
import gtk
from pyruns.run import Run, courses, useGpsElev, useGpsDist
from pyruns.course import Course
from pyruns.summarydata import SummaryData
from pyruns.coords import elevWindow
from pyruns.mapviewer import MapViewer
import pyruns

def main():
    # get the command line options
    cmdOptParser = optparse.OptionParser()
    cmdOptParser.add_option("-f", action = "store", type = "string", dest = "summaryFname", 
                            default = "summary.dat", help = "Name of summary data file")
    cmdOptParser.add_option("-c", action = "store", type = "string", dest = "coursesFname", 
                            default = "courses.dat", help = "Name of courses data file")
    cmdOptParser.add_option("--plotMap", action = "store", type = "string", dest = "plotMap", 
                            default = "", help = "Name of course to plot (all runs) or date (YYYY-MM-DD) of course to plot")
    cmdOptParser.add_option("--plotGoogleMap", action = "store", type = "string", dest = "plotGoogleMap", 
                            default = "", help = "Plots the run given by the date (YYYY-MM-DD) on a google terrain map")
    cmdOptParser.add_option("--elevWindow", action = "store", type = "int", dest = "elevWindow", 
                            default = 5, help = "Window size for smoothing elevations")
    cmdOptParser.add_option("--useGpsDist", action = "store_true", dest = "useGpsDist", 
                            default = False, help = "Use the GPS distance instead of the course distance")
    cmdOptParser.add_option("--useGpsElev", action = "store_true", dest = "useGpsElev", 
                            default = False, help = "Use the GPS/Google elevation instead of the course elevation")
    (options, fnames) = cmdOptParser.parse_args()
    # set params for modules
    pyruns.run.useGpsElev = options.useGpsElev
    pyruns.run.useGpsDist = options.useGpsDist
    pyruns.coords.elevWindow = options.elevWindow
    # get the course data
    pyruns.run.courses = loadCourses(options.coursesFname)
    #    for id in sorted(courses.keys()): courses[id].write(sys.stdout)
    summaryData = SummaryData()
    # first read in previous data from the summary file
    if options.summaryFname != "": summaryData.load(options.summaryFname)
    # now update with any new data
    summaryData.updateFromXML(fnames)
    summaryFile = open(options.summaryFname, "w+")
    summaryData.save(summaryFile)
    summaryFile.close()
    # plot efficiency vs elev rate
    #pyplot.plot(summaryData.getEfficiencies(), summaryData.getElevRates(), "x")
    #pyplot.show()
    if options.plotMap != "":
        runDate = None
        try: 
            runDate = dt.strptime(options.plotMap, "%Y-%m-%d")
            title = "Run " + options.plotMap
        except ValueError: 
            pass
        if runDate == None:
            try:
                title = "Course " + options.plotMap + ":  %.0f miles" % pyruns.run.courses[options.plotMap].dist + \
                    " %.0f feet" % pyruns.run.courses[options.plotMap].elevChange
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
        for run in summaryData.runs:
            if run.coords != None: 
                if (runDate != None and run.startTime.date() == runDate.date()) or run.course == options.plotMap:
                    mapViewer.addTrack(run.coords.getLats(), run.coords.getLngs(), color = colors[i])
                    ax.plot(run.coords.getDists(), run.coords.getMapElevs(), 
                            label = run.getDate() + " (" + ("%.0f" % run.coords.mapChange) + ")", color = colors[i])
                    if maxElev < run.coords.maxElev: maxElev = run.coords.maxElev
                    if minElev > run.coords.minElev: minElev = run.coords.minElev
                    if maxDist < run.dist: maxDist = run.dist
                    found = True
                    i += 1
                    if i == len(colors): i = 0
                    if runDate != None: 
                        title += ":  %.0f miles" % run.dist + " %.0f feet" % run.elevChange
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
        for run in summaryData.runs:
            if run.coords != None: 
                if run.startTime.strftime("%Y-%m-%d") == options.plotGoogleMap:
                    image = run.getGoogleImage()
                    pyplot.imshow(image)
                    pyplot.show()
                    found = True
                    break
        if not found:
            print "*** ERROR: course", options.plotMap, "not found ***"
            sys.exit(0)

def loadCourses(fname):
    courses = {}
    f = open(fname, "r")
    for line in f.readlines():
        if line.strip() == "": continue
        if line.lstrip()[0] == "#": continue
        course = Course.fromString(line)
        if course.id in courses:
            print "Duplicate course", course.id, "skipping..."
            continue
        courses[course.id] = course
    f.close()
    return courses
    


if __name__ == "__main__": main()
