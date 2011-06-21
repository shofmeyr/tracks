#!/usr/bin/python -u 

import sys
import pickle
import os
import numpy
from track import Track
from trackpoints import Trackpoints

class Tracks:
    def __init__(self):
        self.data = {}
        self.index = 0
        self.sorted_keys = []

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def load(self, fname):
        # all the tracks are saved in one pickle file
        f = None
        if os.path.exists(fname): f = open(fname, "r")
        if f != None:
            try: 
                self.data = pickle.load(f)
                f.close()
            except Exception as e: 
                print "Could not load pickle file " + fname + ": " + str(e)
                print "******* get specific exception here"
        self.sorted_keys = sorted(self.data.keys())
        if fname != "" and len(self.data) == 0: 
            print>>sys.stderr, "Found no saved tracks in \"" + fname + "\""
        else: 
            print>>sys.stderr, "Loaded", len(self.data), "tracks from \"" + fname + "\":",\
                self.sorted_keys[0], "to", self.sorted_keys[-1]

    def save(self, fname):
        if fname == "": return
        try:
            f = open(fname, "w+")
            pickle.dump(self.data, f)
            f.close()
        except IOError as e:
            print>>sys.stderr, "Could not save data in " + fname + ": " + str(e)
            return
        print>>sys.stderr, "Saved data for", len(self.data), \
            "tracks, from", self.sorted_keys[0], "to", self.sorted_keys[-1]

    def update_from_xml(self, fnames, tz=None):
        if len(fnames) == 0: return
        tot_time = 0.0
        tot_dist = 0.0
        print>>sys.stderr, "Updating from xml files... "
        for fname in fnames: 
            track = Track.from_xml_file(fname, tz)[0]
            if track is None: continue
            start_time = track.get_start_time_as_str()
            if start_time in self.data: continue
            tot_dist += track.dist
            tot_time += track.duration
            self.data[start_time] = track
            print>>sys.stderr, "Added new track", start_time
        if tot_time > 0: 
            hours = int(tot_time) / int(60)
            mins = tot_time - hours * 60
            print>>sys.stderr, "Updated %.2f miles, %.0f hrs %.0f mins" % (tot_dist, hours, mins)
        else: print>>sys.stderr, "No tracks added"
        self.sorted_keys = sorted(self.data.keys())

    def get_efficiencies(self):
        effs = []
        for track in self: effs.append(track.efficiency)
        return effs

    def get_elev_rates(self):
        elev_rates = []
        for track in self: elev_rates.append(track.elev_rate)
        return elev_rates
    
    def write_days(self, out_file, name, elev_window):
        Track.write_header(out_file)
        for track in self:
            if track.get_start_time_as_str().startswith(name): track.write(out_file, elev_window)

    def write_months(self, out_file, months, elev_window):
        print >> out_file, "#%-12s" % "Month",\
            "%6s" % "dist",\
            "%7s" % "rtime",\
            "%6s" % "mxpc",\
            "%6s" % "avpc",\
            "%5s" % "mxhr",\
            "%5s" % "avhr",\
            "%7s" % "elev",\
            "%6s" % "erate"
        stats = {}
        for field in ["avpc", "mxpc", "avhr", "mxhr", "elev", "erate", "dist", "time"]:
            stats[field] = self.get_monthly_stat(months, field, elev_window)
        for i in range(0, len(months)):
            print >> out_file, \
                "%-13s" % months[i],\
                "%6.2f" % stats["dist"][i],\
                "%7.1f" % stats["time"][i],\
                "%6.2f" % stats["mxpc"][i],\
                "%6.2f" % stats["avpc"][i],\
                "%5.0f" % stats["mxhr"][i],\
                "%5.0f" % stats["avhr"][i],\
                "%7.0f" % stats["elev"][i],\
                "%6.0f" % stats["erate"][i]

    def __iter__(self):
        self.index = 0
        return self

    def next(self):
        if self.index == len(self.sorted_keys) - 1: raise StopIteration
        self.index += 1
        return self.data[self.sorted_keys[self.index]]

    def get_days(self, date_str):
        days = []
        for track in self:
            day_str = track.start_time.strftime("%Y-%m-%d")
            if not day_str.startswith(date_str): continue
            days.append(day_str)
        return days

    def get_months(self, date_str):
        months = []
        first = True
        for track in self:
            month_str = track.start_time.strftime("%Y-%m")
            if not month_str.startswith(date_str): continue
            if first or months[-1] != month_str: months.append(month_str)
            first = False
        return months

    def get_monthly_stat(self, months, field, elev_window):
        monthly_stats = []
        for month in months:
            daily_stats = []
            for track in self:
                month_str = track.start_time.strftime("%Y-%m")
                if not month_str.startswith(month): continue
                stat = track.get_stat(field, elev_window)
                if stat > 0: daily_stats.append(stat)
            if len(daily_stats) == 0: monthly_stats.append(0)
            elif field == "mxpc": monthly_stats.append(min(daily_stats))
            elif field == "mxhr": monthly_stats.append(max(daily_stats))
            elif field == "avpc": monthly_stats.append(numpy.average(daily_stats))
            elif field == "avhr": monthly_stats.append(numpy.average(daily_stats))
            elif field == "erate": monthly_stats.append(numpy.average(daily_stats))
            else: monthly_stats.append(sum(daily_stats))
        return monthly_stats

    def get_daily_stat(self, days, field, elev_window):
        stats = []
        for day in days:
            for track in self:
                day_str = track.start_time.strftime("%Y-%m-%d")
                if not day.startswith(day_str): continue
                stats.append(track.get_stat(field, elev_window))
        return stats

        


