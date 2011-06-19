import sys
import datetime
from trackpoints import Trackpoints

class Track:
    def __init__(self, start_time, duration, dist, max_pace, max_hr, av_hr, trackpoints, comment,
                 known_elev=0, known_dist=0):
        self.start_time = start_time
        self.dist = dist
        self.duration = duration
        self.max_pace = max_pace
        self.max_hr = max_hr
        self.av_hr = av_hr
        self.trackpoints = trackpoints
        self.comment = comment
        self.known_elev = known_elev
        self.known_dist = known_dist

    def __len__(self):
        return len(self.trackpoints)

    @classmethod
    def from_xml_file(cls, fname, tz=None):
        from xmltree import XMLTree
        # load the xml file into a tree
        tree = XMLTree(fname, 
                       namespace={"t":"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}, 
                       root="t:Activities/t:Activity/")
        utc_start_time = tree.find_all("t:Id", is_float=False)[0]
        comment = tree.find_all("t:Comment", is_float=False)
        if len(comment) > 0: comment = comment[0]
        else: comment = ""
        known_elev = tree.find_all("t:KnownElevationMeters")
        if len(known_elev) > 0: known_elev = known_elev[0]
        else: known_elev = 0
        known_dist = tree.find_all("t:KnownDistanceMeters")
        if len(known_dist) > 0: known_dist = known_dist[0]
        else: known_dist = 0

        tree.root += "t:Lap/"
        durations = tree.find_all("t:TotalTimeSeconds")
        duration = sum(durations) / 60.0
        # drop point if the tracktime is too small
        if duration <= 5: 
            print>>sys.stderr, "Dropping", fname, "time is < 5 mins"
            return (None, None)
        try:
            max_pace = max(tree.find_all("t:MaximumSpeed"))
        except ValueError as e: 
            max_pace = 0
        if max_pace > 0: max_pace = 60.0 / (max_pace * Trackpoints.METERS_PER_MILE / 1000.0)
        dist = sum(tree.find_all("t:DistanceMeters")) / Trackpoints.METERS_PER_MILE
        # drop point if the dist is measured, but small
        if dist > 0 and dist < 1.0: 
            print>>sys.stderr, "Dropping", fname, "distance is > 0 and < 1.0"
            return None
        if dist == 0: dist = known_dist / Trackpoints.METERS_PER_MILE
        max_hrs = tree.find_all("t:MaximumHeartRateBpm/t:Value")
        if len(max_hrs) > 0: max_hr = max(max_hrs)
        else: max_hr = 0
        av_hrs = tree.find_all("t:AverageHeartRateBpm/t:Value")
        av_hr = sum([av_hrs[i] * durations[i] / 60 for i in range(0, len(av_hrs))]) / duration
        # drop all points that have low heart rates
        if av_hr < 80 and av_hr > 0: 
            print>>sys.stderr, "Dropping", fname, "av HR is < 80 and > 0"
            return None
        # extract trackpoints from xml
        trackpoints = Trackpoints()
        trackpoints.load_from_xml(tree, fname)
        # FIXME: add an input option to add a comment
        # now write the modified tree back to the file
        f = open(fname, "w")
        tree.write(f)
        f.close()
        # time is UTC, try to convert it here
        lng = None
        if len(trackpoints) > 0: lng =  trackpoints.lngs[0]
        start_time = Track.get_local_time(utc_start_time, lng, tz)
        return (cls(start_time=start_time, duration=duration, dist=dist, 
                    max_pace=max_pace, max_hr=max_hr, av_hr=av_hr, trackpoints=trackpoints, 
                    comment=comment, known_elev=known_elev, known_dist=known_dist), tree)

    @classmethod
    def get_local_time(cls, utc_time_str, lng, tz):
        import pytz
        # FIXME: the time is given as UTC. What is needed is a way to convert the time to the 
        # correct one for the geographic location, as given by the gps coordinates. We use 
        # something very simple here which gives an approximation of the actual time. A better way 
        # to do this is use a timezone service.
        # This can always be corrected later.
        utc_time = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
#        print "utc_time", utc_time
        utc_time = utc_time.replace(tzinfo=pytz.utc)
#        print "UTC replaced", utc_time
        if tz is not None and tz != "": local_time = utc_time.astimezone(pytz.timezone(tz))
        elif lng is not None: local_time = utc_time + datetime.timedelta(hours = int(round(lng / 15.0)))
        else: local_time = utc_time
#        print "Local time", str(local_time)
        return local_time

    def get_stat(self, field, elev_window=0):
        #    FIELDS = ["dist", "time", "mxpc", "avpc", "mxhr", "avhr", "elev", "erate"]
        if field == "dist": return self.dist
        elif field == "time": return self.duration
        elif field == "mxpc": return self.max_pace
        elif field == "avpc": return self.get_av_pace()
        elif field == "mxhr": return self.max_hr
        elif field == "avhr": return self.av_hr
        elif field == "elev": return self.get_elev_change(elev_window)
        elif field == "erate": return self.get_elev_rate(elev_window)

    def get_av_pace(self):
        if self.dist > 0: return self.duration / self.dist
        return 0
        
    def get_elev_rate(self, elev_window):
        elev = self.get_elev_change(elev_window)
        if self.dist > 0: return elev / self.dist
        return 0

    def write(self, out_file, elev_window, time_str=None):
        elev = 0
        elev_rate = 0
        av_pace = self.get_av_pace()
        efficiency = 0
        elev = self.get_elev_change(elev_window)
        elev_rate = self.get_elev_rate(elev_window)
        if self.av_hr > 0 and self.duration > 0:
            efficiency = self.dist * Trackpoints.METERS_PER_MILE / (self.av_hr * self.duration)

        if time_str is None: time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        print >> out_file, \
            "%-20s" % time_str,\
            "%6.2f" % self.dist,\
            "%7.1f" % self.duration,\
            "%5.2f" % self.max_pace,\
            "%5.2f" % av_pace,\
            "%5.0f" % self.max_hr,\
            "%5.0f" % self.av_hr,\
            "%6.0f" % elev,\
            "%6.0f" % (self.known_elev * Trackpoints.FEET_PER_METER),\
            "%5.0f" % elev_rate,\
            "%5.2f" % efficiency,\
            " %s " % self.comment

    @classmethod
    def write_header(cls, out_file):
        print >> out_file, "#%-19s" % "Date & time",\
            "%6s" % "dist",\
            "%7s" % "rtime",\
            "%5s" % "mxpc",\
            "%5s" % "avpc",\
            "%5s" % "mxhr",\
            "%5s" % "avhr",\
            "%6s" % "elev",\
            "%6s" % "kelev",\
            "%5s" % "erate",\
            "%5s" % "eff",\
            " %s " % "comment"

    def get_date(self):
        return self.start_time.strftime("%Y-%m-%d")

    def get_start_time_as_str(self):
        return self.start_time.strftime("%Y-%m-%d-%H%M%S")

    def get_elev_change(self, smoothing_window):
        elev_change = 0
        if self.trackpoints != None: elev_change = self.trackpoints.get_elev_change(smoothing_window)
        if elev_change == 0: return self.known_elev * Trackpoints.FEET_PER_METER
        return elev_change
        
    def get_mid_point_range(self, t):
        if t == "lats": x = self.trackpoints.lats
        else: x = self.trackpoints.lngs
        min_x = min(x)
        max_x = max(x)
        return (min_x + (max_x - min_x) / 2.0, max_x - min_x)

