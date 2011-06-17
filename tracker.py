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
    # cmd_opt_parser.add_argument("-i", action="store", type=str, dest="plot_identical", 
    #                           default="", 
    #                           help="Plot all tracks identical to date (YYYY-MM-DD-HHMMSS)")
    # cmd_opt_parser.add_argument("-s", action="store", type=str, dest="plot_similar", 
    #                           default="", 
    #                           help="Plot all tracks similar to date (YYYY-MM-DD-HHMMSS)")
    # cmd_opt_parser.add_argument("-p", action="store", type=str, dest="fieldsToPlot", 
    #                           default="dist", 
    #                           help="The fields to plot, a comma separated list of up to three of " +\
    #                               "dist,time,avhr,maxhr,avpace,maxpace,hbeats,elev,elevrate")
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
        plot_elevs = PlotXY(track.trackpoints.dists, track.trackpoints.get_elevs(),
                            "Distance (miles)", "Elevation (ft)",
                            "Elevation and heart rate for " + title, 
                            "red", 700, 500, options.elev_window)
        plot_elevs.add_another(track.trackpoints.dists, track.trackpoints.hrs, "Heart Rate (bpm)",
                               "green", options.hr_window)
        plot_elevs.add_another(track.trackpoints.dists, track.trackpoints.get_paces(), 
                               "Pace (mile / min)", "blue", options.pace_window)
        plot_elevs.show_all()
        gtk.main()
    if options.monthly_stats != "":
        (months, dists, paces, hrs, durations) = tracks.get_monthly_stats(options.monthly_stats)
        plot_monthly = PlotXY(months, dists, "", "Distance (miles)",
                             "Monthly distance and pace", "red", 700, 500)
        plot_monthly.add_another(months, paces, "Pace (mile / min)", "green")
        heart_beats = []
        for i in range(0, len(durations)): heart_beats.append(durations[i] * hrs[i] / 1000.0)
        plot_monthly.add_another(months, heart_beats, "heart beats (000's)", "blue")
        plot_monthly.show_all()
        gtk.main()
    if options.daily_stats != "":
        (days, dists, paces, hrs, durations) = tracks.get_daily_stats(options.daily_stats)
        plot_daily = PlotXY(days, dists, "", "Distance (miles)",
                           "Daily distance and pace", color = "red", width = 700, height = 500)
        plot_daily.add_another(days, paces, "Pace (mile / min)", "green")
        heart_beats = []
        for i in range(0, len(durations)): heart_beats.append(durations[i] * hrs[i] / 1000.0)
        plot_daily.add_another(days, heart_beats, "heart beats (000's)", "blue")
        plot_daily.show_all()
        gtk.main()
        

if __name__ == "__main__": main()
