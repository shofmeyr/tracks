import sys
import gtk
import os.path
import gtk.gdk
import gobject

from matplotlib.figure import Figure
#import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
#import matplotlib.pyplot as pyplot

class PlotTracks(gtk.Window):
    def __init__(self, track, title, color, width, height):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.set_default_size(width, height)
        fig = Figure()
        self.ax = fig.add_subplot(111)
        self.ax.get_axes().grid()
        canvas = FigureCanvas(fig)  
        vbox = gtk.VBox()
        vbox.pack_start(canvas)
        toolbar = NavigationToolbar(canvas, self)
        vbox.pack_start(toolbar, False, False)
        self.add(vbox)

        elevChange = track.trackpoints.getElevChange()
        self.ax.plot(track.trackpoints.dists, track.trackpoints.getElevs(),
                     label = track.getDate() + " (" + ("%.0f" % elevChange) + ")", color = color)
        (minElev, maxElev) = track.trackpoints.getMinMaxElevs()
        self.set_title(title)
        maxDist = max(track.trackpoints.dists)
#        self.ax.legend(loc = "lower right", prop = font_manager.FontProperties(size = "x-small"))
        self.ax.axis([0, maxDist, minElev - 50, maxElev + 50])
        self.ax.get_axes().set_xlabel("Distance (miles)")
        self.ax.get_axes().set_ylabel("Elevation (ft)")

