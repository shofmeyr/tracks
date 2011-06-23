#!/usr/bin/python -u 

import argparse
import sys
import gtk
import pytz
from pytracks.tracks import Tracks
from pytracks.maptracks import MapTracks
from pytracks.plotxy import PlotXY
from pytracks.googleearth import GoogleEarth

def plot_bar(x, title, fields, data_func, duration_unit, elev_window=0):
    LABELS = {"dist": "Distance (miles)", "time": "Duration (" + duration_unit +")", 
              "mxpc": "Maximum pace (mins/mile)", "avpc": "Average pace (mins/mile)", 
              "mxhr": "Maximum heart rate (bpm)", "avhr": "Average heart rate (bpm)", 
              "elev": "Elevation gain (ft)", "erate": "Rate of elevation gain (ft/mile)"}
    FIELD_MAX = {"dist": 0, "time": 0, "mxpc": 20.0, "avpc": 20.0, "mxhr": 200, "avhr": 200,
                 "elev": 0, "erate": 0}
    plot = PlotXY(x, "", title, 700, 500, num_series=len(fields))
    colors = ["red", "green", "blue"]
    for i in range(0, len(fields)):
        stat = data_func(x, fields[i], elev_window)
        if stat == None: 
            print stat, "not found"
            return None
        if max(stat) == 0: print "No values found for", fields[i], "skipping"
        else: plot.add_series(stat, LABELS[fields[i]], colors[i], max_y=FIELD_MAX[fields[i]])
    plot.show_all()
    gtk.main()

def main():
    # get the command line options
    cmd_opt_parser = argparse.ArgumentParser(description="Analyze Garmin GPS data",
                                           formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cmd_opt_parser.add_argument("-f", action="store", type=str, dest="tracks_fname", 
                              default="tracks.pck", 
                              help="Name of tracks file containing pickle data")
    cmd_opt_parser.add_argument("-m", action="store", type=str, dest="plot_map", 
                              default="", help="Show track on map for date (YYYY-MM-DD)")
    cmd_opt_parser.add_argument("-e", action="store", type=int, dest="elev_window", 
                              default=2, help="Window size for smoothing elevations")
    cmd_opt_parser.add_argument("-r", action="store", type=int, dest="hr_window", 
                              default=20, help="Window size for smoothing heart rates")
    cmd_opt_parser.add_argument("-c", action="store", type=int, dest="pace_window", 
                              default=20, help="Window size for smoothing paces")
    cmd_opt_parser.add_argument("-t", action="store_true", dest="show_terrain", 
                              default=False, help="Show terrain on map instead of aerial photo")
    cmd_opt_parser.add_argument("-z", action="store", type=str, dest="tz", 
                              default="US/Pacific", help="Set time zone for xml conversion")
    cmd_opt_parser.add_argument("-n", action="store", type=str, dest="monthly_stats", 
                              default="", help="Plot monthly stats for substring of YYYY-MM")
    cmd_opt_parser.add_argument("-d", action="store", type=str, dest="daily_stats", 
                              default="", help="Plot daily stats for substring YYYY-MM-DD")
    cmd_opt_parser.add_argument("-k", action="store", type=str, dest="google_earth", 
                              default="", help="Show track on Google Earth for date (YYYY-MM-DD)")
    FIELDS = ["dist", "time", "mxpc", "avpc", "mxhr", "avhr", "elev", "erate"]
    field_str = ""
    for field in FIELDS: 
        field_str += field
        if field != FIELDS[-1]:  field_str += ", "
    cmd_opt_parser.add_argument("-p", action="store", type=str, dest="fields_to_plot", 
                                default="dist", 
                                help="The fields to plot for daily or monthly. " + \
                                    "A comma separated list of up to three of " + \
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
    if options.tz != "auto" and options.tz not in pytz.common_timezones:
        print "Timezone not found. Are you looking for one of the following?"
        num_tzs = 0
        for tz in pytz.common_timezones:
            if tz.startswith(options.tz): 
                print tz
                num_tzs += 1
        if num_tzs == 0: 
            for tz in pytz.common_timezones: print tz
            
        sys.exit(0)
    tracks = Tracks()
    tracks.load(options.tracks_fname)
    # now update with any new data
    tracks.update_from_xml(options.fnames, options.tz)
    if len(tracks) == 0: 
        print>>sys.stderr, "No tracks found"
        sys.exit(0)
    tracks.save(options.tracks_fname)
    track_name = options.plot_map
    if track_name == "": track_name = options.google_earth
    if track_name != "":
        try:
            track = tracks[track_name]
        except:
            print "Cannot find track for", track_name
            sys.exit(0)
        track.write_header(sys.stdout)
        track.write(sys.stdout, options.elev_window)
        if len(track) == 0: 
            print "Track", track_name, "has no trackpoints to map"
            sys.exit(0)
        title = "Track %s, %.1f m, %.0f ft" % (track_name, track.dist, 
                                               track.get_elev_change(options.elev_window))
        if options.plot_map != "":
            map_tracks = MapTracks(track, "Map of " + title, color="red", width=800, height=600, 
                                   show_terrain=options.show_terrain)
            map_tracks.show_all()
        else:
            GoogleEarth.show_in_google_earth(track)
        
        plot_elevs = PlotXY(track.trackpoints.dists, "Distance (miles)", 
                            "Elevation and heart rate for " + title, 
                            700, 500)
        plot_elevs.add_series(track.trackpoints.get_elevs(), "Elevation (ft)", "red", 
                              options.elev_window)
        plot_elevs.add_series(track.trackpoints.hrs, "Heart Rate (bpm)", "green", 
                              options.hr_window)
        plot_elevs.add_series(track.trackpoints.get_paces(), "Pace (mile / min)", "blue", 
                              options.pace_window)
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
    if options.monthly_stats != "":
        months = tracks.get_months(options.monthly_stats)
        tracks.get_daily_stat
        tracks.write_months(sys.stdout, months, options.elev_window)
        plot_bar(months, "Monthly stats for " + options.monthly_stats, fields, tracks.get_monthly_stat,
                 "hours", options.elev_window)
    if options.daily_stats != "":
        days = tracks.get_days(options.daily_stats)
        tracks.write_days(sys.stdout, options.daily_stats, options.elev_window)
        plot_bar(days, "Daily stats for " + options.daily_stats, fields, tracks.get_daily_stat,
                 "mins", options.elev_window)

if __name__ == "__main__": main()
