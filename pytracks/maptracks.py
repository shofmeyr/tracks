#!/usr/bin/python

import sys
import gtk
import os.path
import gtk.gdk
import gobject


gobject.threads_init()
gtk.gdk.threads_init()

#Try static lib first
mydir = os.path.dirname(os.path.abspath(__file__))
libdir = os.path.abspath(os.path.join(mydir, "..", "python", ".libs"))
sys.path.insert(0, libdir)

import osmgpsmap

class MapTracks(gtk.Window):
    def __init__(self, showTerrain = False):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(800, 800)
        self.connect('destroy', lambda x: gtk.main_quit())
#        self.set_title(title)
        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)
#        self.osm = osmgpsmap.GpsMap(repo_uri = "http://acetate.geoiq.com/tiles/acetate-hillshading/#Z/#X/#Y.png")
#        self.osm = osmgpsmap.GpsMap(repo_uri = "http://mt1.google.com/vt/x=#X&y=#Y&z=#Z")
        if showTerrain:
            self.osm = osmgpsmap.GpsMap(repo_uri = "http://khm.google.com/vt/lbw/lyrs=p&x=#X&y=#Y&z=#Z")
        else:
            self.osm = osmgpsmap.GpsMap(repo_uri = "http://mt1.google.com/vt/lyrs=y&x=#X&y=#Y&z=#Z")
#        self.osm = osmgpsmap.GpsMap(repo_uri = "http://tile.openstreetmap.org/#Z/#X/#Y.png")
        self.osm.layer_add(osmgpsmap.GpsMapOsd(show_dpad = True, show_zoom = True))
        self.osm.connect('button_release_event', self.mapClicked)
#        self.osm.connect("motion_notify_event", self.updateDistance)
        #connect keyboard shortcuts
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_FULLSCREEN, gtk.gdk.keyval_from_name("F11"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_UP, gtk.gdk.keyval_from_name("Up"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_DOWN, gtk.gdk.keyval_from_name("Down"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_LEFT, gtk.gdk.keyval_from_name("Left"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_RIGHT, gtk.gdk.keyval_from_name("Right"))
        self.vbox.pack_start(self.osm)
        self.statusBar = gtk.Statusbar()
        self.vbox.pack_start(self.statusBar, False, False, 0)
#        gobject.timeout_add(500, self.updateDistance)
        
    def addTracks(self, tracks, trackDates, colors):
        colorIndex = 0
        found = False
        for trackDate in trackDates:
            try: track = tracks[trackDate]
            except: continue
            if len(track) == 0: continue
            found = True
            # create the track
            mapTrack = osmgpsmap.GpsMapTrack()
            mapTrack.set_property("line-width", 2)
            mapTrack.set_property("color", gtk.gdk.color_parse(colors[colorIndex]))
            colorIndex += 1
            if colorIndex == len(colors): break
            for i in range(0, len(track.trackpoints)): 
                mapTrack.add_point(osmgpsmap.point_new_degrees(track.trackpoints.lats[i], track.trackpoints.lngs[i]))
            self.osm.track_add(mapTrack)
            # center the track
            (centerLat, latRange) = track.getMidPointRange("lats")
            (centerLng, lngRange) = track.getMidPointRange("lngs")
            maxRange = max(latRange, lngRange)
            if maxRange > 0.04: zoom = 14
            else: zoom = 15
            self.osm.set_center_and_zoom(latitude = centerLat, longitude = centerLng, zoom = zoom)
            # TODO: add numbers every 1/2 mile on the track. We'll need an image for each number to do this
            #        pb = gtk.gdk.pixbuf_new_from_file_at_size (num + ".png", 24, 24)
            #        self.osm.image_add(lat, lon, pb)
        return found

    def mapClicked(self, osm, event):
        lat,lon = self.osm.get_event_location(event).get_degrees()
        if event.button == 1:
            self.statusBar.push(1, str(lat) + "," + str(lon))
            pass
        elif event.button == 2:
            self.osm.gps_add(lat, lon, heading=osmgpsmap.INVALID);
        elif event.button == 3:
            pb = gtk.gdk.pixbuf_new_from_file_at_size ("num.png", 24, 24)
            self.osm.image_add(lat, lon, pb)

    def updateDistance(self, osm, event):
        p = osmgpsmap.point_new_degrees(self.minLat, self.minLng)
        self.osm.convert_screen_to_geographic(int(event.x), int(event.y), p)
        self.statusBar.push(1, str(self.minLat + p.rlat) + "," + str(self.minLng + p.rlon))


if __name__ == "__main__":
    u = MapTracks()
    u.show_all()
    gtk.main()

