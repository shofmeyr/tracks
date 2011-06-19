#!/usr/bin/python -u 

import argparse
import sys
import gtk
from pytracks.tracks import Tracks
from pytracks.maptracks import MapTracks
from pytracks.plotxy import PlotXY

def main():
    # get the command line options
    cmd_opt_parser = argparse.ArgumentParser(description="Analyze Garmin GPS data",
                                           formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cmd_opt_parser.add_argument("-f", action="store", type=str, dest="tracks_fname", 
                              default="tracks.pck", 
                              help="Name of tracks file containing pickle data")
    cmd_opt_parser.add_argument("-m", action="store", type=str, dest="plot_map", 
                              default="", 
                              help="Show track on map for date (YYYY-MM-DD)")
    cmd_opt_parser.add_argument("-e", action="store", type=int, dest="elev_window", 
                              default=2, help="Window size for smoothing elevations")
    cmd_opt_parser.add_argument("-r", action="store", type=int, dest="hr_window", 
                              default=20, help="Window size for smoothing heart rates")
    cmd_opt_parser.add_argument("-c", action="store", type=int, dest="pace_window", 
                              default=20, help="Window size for smoothing paces")
    cmd_opt_parser.add_argument("-t", action="store_true", dest="show_terrain", 
                              default=False, help="Show terrain on map instead of aerial photo")
    cmd_opt_parser.add_argument("-z", action="store", type=str, dest="tz", 
                              default="US/Pacific", 
                              help="Set time zone for xml conversion")
    cmd_opt_parser.add_argument("-n", action="store", type=str, dest="monthly_stats", 
                              default="", 
                              help="Plot monthly stats for substring of YYYY-MM")
    cmd_opt_parser.add_argument("-d", action="store", type=str, dest="daily_stats", 
                              default="", 
                              help="Plot daily stats for substring YYYY-MM-DD")
    FIELDS = ["dist", "time", "mxpc", "avpc", "mxhr", "avhr", "elev", "erate"]
    field_str = ""
    for field in FIELDS: field_str += field + ","
    cmd_opt_parser.add_argument("-p", action="store", type=str, dest="fields_to_plot", 
                                default="dist", 
                                help="The fields to plot for daily or monthly." + \
                                    "a comma separated list of up to three of " + \
                                    field_str)
    # cmd_opt_parser.add_argument("-i", action="store", type=str, dest="plot_identical", 
    #                           default="", 
    #                           help="Plot all tracks identical to date (YYYY-MM-DD-HHMMSS)")
    # cmd_opt_parser.add_argument("-s", action="store", type=str, dest="plot_similar", 
    #                           default="", 
    #                           help="Plot all tracks similar to date (YYYY-MM-DD-HHMMSS)")
    cmd_opt_parser.add_argument("fnames", metavar='N', type=str, nargs='*',
                              help="a list of xml files containing TCX data")
    options = cmd_opt_parser.parse_args()

    tracks = Tracks()
    tracks.load(options.tracks_fname)
    # now update with any new data
    tracks.update_from_xml(options.fnames, options.tz)
    if len(tracks) == 0: 
        print>>sys.stderr, "No tracks found"
        sys.exit(0)
    tracks.save(options.tracks_fname)
    if options.plot_map != "": 
        try:
            track = tracks[options.plot_map]
        except:
            print "Cannot find track for", options.plot_map
            sys.exit(0)
        if len(track) == 0: 
            print "Track", options.plot_map, "has no trackpoints"
            sys.exit(0)
        title = "Track %s, %.1f m, %.0f ft" % (options.plot_map, track.dist, 
                                               track.get_elev_change(options.elev_window))
        map_tracks = MapTracks(track, "Map of " + title, color="red", width=800, height=600, 
                               show_terrain=options.show_terrain)
        map_tracks.show_all()
        
        plot_elevs = PlotXY(track.trackpoints.dists, "Distance (miles)", "Elevation and heart rate for " + title, 
                            700, 500)
        plot_elevs.add_series(track.trackpoints.get_elevs(), "Elevation (ft)", "red", options.elev_window)
        plot_elevs.add_series(track.trackpoints.hrs, "Heart Rate (bpm)", "green", options.hr_window)
        plot_elevs.add_series(track.trackpoints.get_paces(), "Pace (mile / min)", "blue", options.pace_window)
        plot_elevs.show_all()
        gtk.main()

    fields = options.fields_to_plot.split(",")
    if len(fields) > 3: 
        print  "Too many fields, max of 3"
        return
    for field in fields:
        if field not in FIELDS:
            print field, "is an invalid field, must be one of", FIELDS
            return
    labels = {"dist": "Distance (miles)", "time": "Duration (hrs)", "mxpc": "Maximum pace (minm/mile)", 
              "avpc": "Average pace (mins/mile)", "mxhr": "Maximum heart rate (bpm)", 
              "avhr": "Average heart rate (bpm)", "elev": "Elevation gain (ft)", 
              "erate": "Rate of elevation gain (ft/mile)"}
    if options.monthly_stats != "":
        months = tracks.get_months(options.monthly_stats)
        write_header = True
        for month in months:
            tracks.write(sys.stdout, month, options.elev_window, only_total=True, write_header=write_header)
            write_header = False
        tracks.write(sys.stdout, options.monthly_stats, options.elev_window, only_total=True, write_header=False)
        plot_monthly = PlotXY(months, "", "Monthly stats for " + options.monthly_stats, 700, 500)
        colors = ["red", "green", "blue"]
        for i in range(0, len(fields)):
            stat = tracks.get_monthly_stat(options.monthly_stats, fields[i], options.elev_window)
            if stat == None: 
                print stat, "not found"
                return None
            if fields[i] == "time": stat = [s / 60.0 for s in stat]
            plot_monthly.add_series(stat, labels[fields[i]], colors[i])
        plot_monthly.show_all()
        gtk.main()
    if options.daily_stats != "":
        days = tracks.get_days(options.daily_stats)
        tracks.write(sys.stdout, options.daily_stats, options.elev_window)
        plot_daily = PlotXY(days, "", "Daily stats for " + options.daily_stats, width = 700, height = 500)
        colors = ["red", "green", "blue"]
        for i in range(0, len(fields)):
            stat = tracks.get_daily_stat(options.daily_stats, fields[i], options.elev_window)
            if stat == None: 
                print stat, "not found"
                return None
            plot_daily.add_series(stat, labels[fields[i]], colors[i])
        plot_daily.show_all()
        gtk.main()
        

if __name__ == "__main__": main()
