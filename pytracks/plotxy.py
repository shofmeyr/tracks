import numpy
import gtk
import sys
import datetime
import calendar
import matplotlib.dates
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

class PlotXY(gtk.Window):
    def __init__(self, x, x_label, title, width, height, num_series=3):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        if not x: 
            print "No x values in plot"
            sys.exit(0)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.set_default_size(width, height)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.offset = 0
        self.set_title(title)
        self.ax.get_axes().set_xlabel(x_label)
        self.ax.get_axes().grid()
        if isinstance(x[0],str): self.fig.autofmt_xdate()
        canvas = FigureCanvas(self.fig)  
        vbox = gtk.VBox()
        vbox.pack_start(canvas)
        toolbar = NavigationToolbar(canvas, self)
        vbox.pack_start(toolbar, False, False)
        self.add(vbox)
        self.x = x
        self.num_series = num_series

    def add_series(self, y, y_label, color, smoothing_window=0, max_y=0):
        if len(self.x) != len(y): 
            print "Warning", len(self.x), "x values in plot but", len(y), \
                "y values (" + y_label + "), truncating"
            if len(self.x) < len(y): y = y[:len(self.x)]
            elif len(y) < len(self.x): self.x = self.x[:len(y)]
        if smoothing_window > 0:
            smoothed_y = []
            for i in range(smoothing_window, len(y) - smoothing_window): 
                smoothed_y.append(numpy.average(y[i - smoothing_window:i + smoothing_window]))
            y = smoothed_y
            self.x = self.x[:len(y)]
        if self.offset > 0:
            ax2 = self.ax.twinx()
            self.fig.subplots_adjust(right = 0.8)
            ax2.spines["right"].set_position(("axes", 1 + (self.offset - 1.0) * 0.15))
            PlotXY._make_patch_spines_invisible(ax2)
            PlotXY._make_spine_invisible(ax2, "right")
        else:
            ax2 = self.ax
        # plot this with string values on the x-axis 
        if isinstance(self.x[0], str):
            if len(self.x[0]) == 7: 
                fmt = "%Y-%m"
                # we have to be small enough so that feb doesn't overlap, i.e. 28 days
                bar_width = 27.0 / self.num_series
            else: 
                fmt = "%Y-%m-%d"
                # 1.0 is one day
                bar_width = 0.95 / self.num_series
            dates = []
            for x_i in self.x:
#                calendar.monthrange(int(x_i[:4]), int(x_i[5:7]))[1]
                dates.append(matplotlib.dates.date2num(datetime.datetime.strptime(x_i, fmt)))
            for i in range(0, len(dates)): dates[i] += (bar_width * self.offset)
            ax2.bar(dates, y, color=color, width=bar_width, linewidth=0)
            # mask out the 0 values
#            y = numpy.ma.array(y)
#            y = numpy.ma.masked_where(y == 0, y)
#            ax2.plot_date(dates, y, color=color, ls="-")
            ax2.xaxis_date()
            if max_y == 0: max_y = max(y) * 1.05
            ax2.set_ylim(0, max_y)
        else: 
            ax2.plot(self.x, y, color=color)
            ax2.set_ylim(min(y) * 0.95, max(y) * 1.05)
        ax2.set_ylabel(y_label, color = color)
        ax2.get_axes().grid()
        for tl in ax2.get_yticklabels(): tl.set_color(color)
        self.offset += 1


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

