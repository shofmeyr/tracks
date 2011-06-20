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
    
    def write_header(self, out_file):
        Track.write_header(out_file)
        
    def write(self, out_file, name = "all", elev_window=2, only_total=False):
        track_tot = Track(start_time=None, duration=0, dist=0, max_pace=100, max_hr=0,
                         av_hr=0, trackpoints=None, comment="", known_elev=0)
        num_tracks_for_hr = 0.0
        for track in self:
            if track.get_start_time_as_str().startswith(name):
                if track_tot.start_time is None: track_tot.start_time = track.start_time
                track_tot.duration += track.duration
                track_tot.dist += track.dist
                if track.max_pace > 0 and track.max_pace < track_tot.max_pace: 
                    track_tot.max_pace = track.max_pace
                if track.max_hr > track_tot.max_hr and track.max_hr < 190: track_tot.max_hr = track.max_hr
                track_tot.av_hr += track.av_hr
                if track.av_hr > 0: num_tracks_for_hr += 1
                track_tot.known_elev += (track.get_elev_change(elev_window) / Trackpoints.FEET_PER_METER)
                if not only_total: track.write(out_file, elev_window)
        # now print summary
        if track_tot.max_pace == 100: track_tot.max_pace = 0
        if num_tracks_for_hr > 0: track_tot.av_hr /= num_tracks_for_hr
        track_tot.write(out_file, elev_window, name)

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

        


