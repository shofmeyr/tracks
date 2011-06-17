import numpy
import gtk
import datetime
import matplotlib.dates
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

class PlotXY(gtk.Window):
    def __init__(self, x, y, xLabel, yLabel, title, color, width, height, smoothing_window=0):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.set_default_size(width, height)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        PlotXY._plot_axes(x, y, self.ax, color, smoothing_window)
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

    def add_another(self, x, y, yLabel, color, smoothing_window=0):
        ax2 = self.ax.twinx()
        PlotXY._plot_axes(x, y, ax2, color, smoothing_window)
        self.fig.subplots_adjust(right = 0.8)
        ax2.spines["right"].set_position(("axes", 1 + self.offset))
        self.offset += 0.15
        PlotXY._make_patch_spines_invisible(ax2)
        PlotXY._make_spine_invisible(ax2, "right")
        ax2.set_ylabel(yLabel, color = color)
        for tl in ax2.get_yticklabels(): tl.set_color(color)

    @classmethod
    def _plot_axes(cls, x, y, ax, color, smoothing_window):
        if len(x) != len(y): 
            print "Warning", len(x), "x values in plot but", len(y), "y values, truncating"
            if len(x) < len(y): y = y[:len(x)]
            elif len(y) < len(x): x = x[:len(y)]
        if smoothing_window > 0:
            smoothed_y = []
            for i in range(smoothing_window, len(y) - smoothing_window): 
                smoothed_y.append(numpy.average(y[i - smoothing_window:i + smoothing_window]))
            y = smoothed_y
            x = x[:len(y)]
        # plot this with string values on the x-axis 
        if isinstance(x[0], str):
            if len(x[0]) == 7: fmt = "%Y-%m"
            else: fmt = "%Y-%m-%d"
            dates = [matplotlib.dates.date2num(datetime.datetime.strptime(d, fmt)) for d in x]
            # mask out the 0 values
            y = numpy.ma.array(y)
            y = numpy.ma.masked_where(y == 0, y)
            ax.plot_date(dates, y, color=color, ls="-")
        else: 
            ax.plot(x, y, color=color)
            ax.axis([min(x), max(x), min(y) * 0.95, max(y) * 1.05])

    @classmethod
    def _make_patch_spines_invisible(cls, ax):
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.itervalues(): sp.set_visible(False)

    @classmethod
    def _make_spine_invisible(cls, ax, direction):
        if direction in ["right", "left"]:
            ax.yaxis.set_ticks_position(direction)
            ax.yaxis.set_label_position(direction)
        elif direction in ["top", "bottom"]:
            ax.xaxis.set_ticks_position(direction)
            ax.xaxis.set_label_position(direction)
        else:
            raise ValueError("Unknown Direction : %s" % (direction,))
        ax.spines[direction].set_visible(True)

