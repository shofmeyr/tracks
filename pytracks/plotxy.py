import sys, numpy, gtk, os.path, gtk.gdk, gobject

from matplotlib.figure import Figure
from matplotlib.spines import Spine
#import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
#import matplotlib.pyplot as pyplot

class PlotXY(gtk.Window):
    def __init__(self, x, y, xLabel, yLabel, title, color, width, height, smoothingWindow = 0):
        if len(x) != len(y): 
            print "Warning", len(x), "x values in plot (" + xLabel + ") but", \
                len(y), "y values (" + yLabel, "truncating"
            if len(x) < len(y): y = y[:len(x)]
            elif len(y) < len(x): x = x[:len(y)]
        if smoothingWindow > 0:
            smoothedY = []
            for i in range(smoothingWindow, len(y) - smoothingWindow): 
                smoothedY.append(numpy.average(y[i - smoothingWindow:i + smoothingWindow]))
            y = smoothedY
            x = x[:len(y)]
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
        # plot this with string values on the x-axis 
        if type(x[0]) == str: self.ax.bar(x, y, color = color)
        else: 
            self.ax.plot(x, y, color = color)
            self.ax.axis([min(x), max(x), min(y) * 0.95, max(y) * 1.05])
        self.set_title(title)
#        self.ax.legend(loc = "lower right", prop = font_manager.FontProperties(size = "x-small"))
        self.ax.get_axes().set_xlabel(xLabel)
        self.ax.get_axes().set_ylabel(yLabel, color = color)
        for tick in self.ax.yaxis.get_major_ticks(): tick.label.set_color(color)

    def addSecond(self, x, y, yLabel, color, smoothingWindow = 0):
        if len(x) != len(y): 
            print "Warning", len(x), "x values in plot but", \
                len(y), "y values (" + yLabel, "truncating"
            if len(x) < len(y): y = y[:len(x)]
            elif len(y) < len(x): x = x[:len(y)]
        if smoothingWindow > 1:
            smoothedY = []
            for i in range(0, len(y) - smoothingWindow): 
                smoothedY.append(numpy.average(y[i:i + smoothingWindow]))
            y = smoothedY
            x = x[:len(y)]
        ax2 = self.ax.twinx()
        if type(x[0]) == str: ax2.bar(x, y, color)
        else: 
            ax2.plot(x, y, color)
            ax2.axis([min(x), max(x), min(y) * 0.95, max(y) * 1.05])
        ax2.set_ylabel(yLabel, color = color)
        for tick in ax2.yaxis.get_major_ticks(): tick.label.set_color(color)

