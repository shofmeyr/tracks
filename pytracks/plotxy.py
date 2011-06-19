import numpy
import gtk
import datetime
import matplotlib.dates
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

class PlotXY(gtk.Window):
    def __init__(self, x, xLabel, title, width, height):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.set_default_size(width, height)
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.offset = 0
        self.set_title(title)
        self.ax.get_axes().set_xlabel(xLabel)
        self.ax.get_axes().grid()
        if isinstance(x[0],str): self.fig.autofmt_xdate()
        canvas = FigureCanvas(self.fig)  
        vbox = gtk.VBox()
        vbox.pack_start(canvas)
        toolbar = NavigationToolbar(canvas, self)
        vbox.pack_start(toolbar, False, False)
        self.add(vbox)
        self.x = x

    def add_series(self, y, yLabel, color, smoothing_window=0):
        if self.offset > 0:
            ax2 = self.ax.twinx()
            self.fig.subplots_adjust(right = 0.8)
            ax2.spines["right"].set_position(("axes", 1 + (self.offset - 1.0) * 0.15))
            PlotXY._make_patch_spines_invisible(ax2)
            PlotXY._make_spine_invisible(ax2, "right")
        else:
            ax2 = self.ax
        self._plot_axes(y, ax2, color, smoothing_window, self.offset)
        ax2.set_ylabel(yLabel, color = color)
        ax2.get_axes().grid()
        for tl in ax2.get_yticklabels(): tl.set_color(color)
        self.offset += 1

    def _plot_axes(self, y, ax, color, smoothing_window, offset):
        if len(self.x) != len(y): 
            print "Warning", len(self.x), "x values in plot but", len(y), "y values, truncating"
            if len(self.x) < len(y): y = y[:len(self.x)]
            elif len(y) < len(self.x): self.x = x[:len(y)]
        if smoothing_window > 0:
            smoothed_y = []
            for i in range(smoothing_window, len(y) - smoothing_window): 
                smoothed_y.append(numpy.average(y[i - smoothing_window:i + smoothing_window]))
            y = smoothed_y
            self.x = self.x[:len(y)]
        # plot this with string values on the x-axis 
        if isinstance(self.x[0], str):
            if len(self.x[0]) == 7: fmt = "%Y-%m"
            else: fmt = "%Y-%m-%d"
            min_diff = 100000
            prev_date = None
            dates = []
            for x_i in self.x:
                dates.append(matplotlib.dates.date2num(datetime.datetime.strptime(x_i, fmt)))
                if prev_date is not None:
                    date_diff = dates[-1] - prev_date
                    if date_diff < min_diff: min_diff = date_diff
                prev_date = dates[-1]
            bar_width = min_diff / 4
            if bar_width < 0.3: bar_width = 0.3
            for i in range(0, len(dates)): dates[i] += (bar_width * offset)
            ax.bar(dates, y, color=color, width=bar_width, linewidth=0)
            # mask out the 0 values
#            y = numpy.ma.array(y)
#            y = numpy.ma.masked_where(y == 0, y)
#            ax.plot_date(dates, y, color=color, ls="-")
            ax.xaxis_date()
        else: 
            ax.plot(self.x, y, color=color)
            ax.axis([min(self.x), max(self.x), min(y) * 0.95, max(y) * 1.05])

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

