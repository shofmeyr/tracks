#!/usr/bin/python -u 

import sys
import pickle
import os
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
    
    def write(self, out_file, name = "all", elev_window=2):
        Track.write_header(out_file)
        track_tot = Track(start_time=None, duration=0, dist=0, max_pace=0, max_hr=0,
                         av_hr=0, trackpoints=None, comment="", known_elev=0)
        num_tracks_for_hr = 0.0
        for track in self:
            if track.get_start_time_as_str().startswith(name):
                if track_tot.start_time is None: track_tot.start_time = track.start_time
                track_tot.duration += track.duration
                track_tot.dist += track.dist
                if track.max_pace > track_tot.max_pace: track_tot.max_pace = track.max_pace
                if track.max_hr > track_tot.max_hr and track.max_hr < 190: track_tot.max_hr = track.max_hr
                track_tot.av_hr += track.av_hr
                if track.av_hr > 0: num_tracks_for_hr += 1
                track_tot.known_elev += (track.get_elev_change(elev_window) / Trackpoints.FEET_PER_METER)
                track.write(out_file, elev_window)
        # now print summary
        track_tot.av_hr /= num_tracks_for_hr
        track_tot.write(out_file, elev_window, name)

    def __iter__(self):
        self.index = 0
        return self

    def next(self):
        if self.index == len(self.sorted_keys) - 1: raise StopIteration
        self.index += 1
        return self.data[self.sorted_keys[self.index]]

    def get_monthly_stats(self, date_str):
        months = []
        dists = []
        paces = []
        hrs = []
        durations = []
        dist = 0
        duration = 0
        pace_duration = 0
        heart_beats = 0
        hr_duration = 0
        i = 0
        curr_month_str = None
        for track in self:
            month_str = track.start_time.strftime("%Y-%m")
            if not month_str.startswith(date_str): continue
            if curr_month_str is None: curr_month_str = month_str
            if curr_month_str != month_str: 
                months.append(curr_month_str)
                dists.append(dist)
                paces.append(pace_duration)
                if hr_duration > 0: hrs.append(heart_beats / hr_duration)
                else: hrs.append(0)
                durations.append(duration)
                dist = 0
                duration = 0
                pace_duration = 0
                heart_beats = 0
                hr_duration = 0
                curr_month_str = month_str
            dist += track.dist
            duration += track.duration
            if track.dist > 0: pace_duration += track.duration
            if track.av_hr > 0:
                heart_beats += (track.av_hr * track.duration)
                hr_duration += track.duration
            i += 1
        else:   # make sure we get the last month
            months.append(curr_month_str)
            dists.append(dist)
            paces.append(pace_duration)
            if hr_duration > 0: hrs.append(heart_beats / hr_duration)
            else: hrs.append(0)
            durations.append(duration)
        print "%-9s" % "months", "%5s" % "time", "%5s" % "dist", "%5s" % "pace"
        for i in range(0, len(paces)): 
            if dists[i] > 0: paces[i] /= dists[i]
            else: paces[i] = 0
            if paces[i] > 25: paces[i] = 0
            print "%-9s" % months[i], "%5.1f" % (durations[i] / 60), "%5.0f" % dists[i], "%5.1f" % paces[i]
        return (months, dists, paces, hrs, durations)

    def get_daily_stats(self, date_str):
        days = []
        dists = []
        paces = []
        hrs = []
        durations = []
        for d in self:
            day_str = d.start_time.strftime("%Y-%m-%d")
            if not day_str.startswith(date_str): continue
            days.append(day_str)
            dists.append(d.dist)
            paces.append(d.duration)
            durations.append(d.duration)
            hrs.append(d.av_hr)
        for i in range(0, len(paces)): 
            if dists[i] > 0: paces[i] /= dists[i]
            else: paces[i] = 0
        self.write(sys.stdout, date_str)
        return (days, dists, paces, hrs, durations)

        


