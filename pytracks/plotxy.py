import sys, numpy, gtk, os.path, gtk.gdk, gobject, datetime

import matplotlib.dates
from matplotlib.figure import Figure
#import matplotlib.font_manager as font_manager
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
#import matplotlib.pyplot as pyplot

class PlotXY(gtk.Window):
    def __init__(self, x, y, xLabel, yLabel, title, color, width, height, smoothingWindow = 0):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.set_default_size(width, height)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        PlotXY._plotAxes(x, y, self.ax, color, smoothingWindow)
        if type(x[0]) == str: self.fig.autofmt_xdate()
        self.offset = 0
        self.set_title(title)
#        self.ax.legend(loc = "lower right", prop = font_manager.FontProperties(size = "x-small"))
        self.ax.get_axes().set_xlabel(xLabel)
        self.ax.get_axes().set_ylabel(yLabel, color = color)
        self.ax.get_axes().grid()
        for tl in self.ax.get_yticklabels(): tl.set_color(color)
        canvas = FigureCanvas(self.fig)  
        vbox = gtk.VBox()
        vbox.pack_start(canvas)
        toolbar = NavigationToolbar(canvas, self)
        vbox.pack_start(toolbar, False, False)
        self.add(vbox)

    def addAnother(self, x, y, yLabel, color, smoothingWindow = 0):
        ax2 = self.ax.twinx()
        PlotXY._plotAxes(x, y, ax2, color, smoothingWindow)
        self.fig.subplots_adjust(right = 0.8)
        ax2.spines["right"].set_position(("axes", 1 + self.offset))
        self.offset += 0.15
        PlotXY._makePatchSpinesInvisible(ax2)
        PlotXY._makeSpineInvisible(ax2, "right")
        ax2.set_ylabel(yLabel, color = color)
        for tl in ax2.get_yticklabels(): tl.set_color(color)

    @classmethod
    def _plotAxes(cls, x, y, ax, color, smoothingWindow):
        if len(x) != len(y): 
            print "Warning", len(x), "x values in plot but", len(y), "y values, truncating"
            if len(x) < len(y): y = y[:len(x)]
            elif len(y) < len(x): x = x[:len(y)]
        if smoothingWindow > 0:
            smoothedY = []
            for i in range(smoothingWindow, len(y) - smoothingWindow): 
                smoothedY.append(numpy.average(y[i - smoothingWindow:i + smoothingWindow]))
            y = smoothedY
            x = x[:len(y)]
        # plot this with string values on the x-axis 
        if type(x[0]) == str: 
            if len(x[0]) == 7: fmt = "%Y-%m"
            else: fmt = "%Y-%m-%d"
            dates = [matplotlib.dates.date2num(datetime.datetime.strptime(d, fmt)) for d in x]
            ax.plot_date(dates, y, color = color, ls = '-')
        else: 
            ax.plot(x, y, color = color)
            ax.axis([min(x), max(x), min(y) * 0.95, max(y) * 1.05])

    @classmethod
    def _makePatchSpinesInvisible(cls, ax):
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.itervalues(): sp.set_visible(False)

    @classmethod
    def _makeSpineInvisible(cls, ax, direction):
        if direction in ["right", "left"]:
            ax.yaxis.set_ticks_position(direction)
            ax.yaxis.set_label_position(direction)
        elif direction in ["top", "bottom"]:
            ax.xaxis.set_ticks_position(direction)
            ax.xaxis.set_label_position(direction)
        else:
            raise ValueError("Unknown Direction : %s" % (direction,))
        ax.spines[direction].set_visible(True)
