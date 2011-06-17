#!/usr/bin/python

import gtk
import gtk.gdk
import osmgpsmap

class MapTracks(gtk.Window):
    def __init__(self, track, title, color, width, height, show_terrain):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(width, height)
        self.connect('destroy', lambda x: gtk.main_quit())
        self.vbox = gtk.VBox(False, 0)
        self.add(self.vbox)
#        self.osm = osmgpsmap.GpsMap(repo_uri = "http://acetate.geoiq.com/tiles/acetate-hillshading/#Z/#X/#Y.png")
        if show_terrain:
            self.osm = osmgpsmap.GpsMap(repo_uri=
                                        "http://khm.google.com/vt/lbw/lyrs=p&x=#X&y=#Y&z=#Z")
        else:
            self.osm = osmgpsmap.GpsMap(repo_uri="http://mt1.google.com/vt/lyrs=y&x=#X&y=#Y&z=#Z")
#        self.osm = osmgpsmap.GpsMap(repo_uri="http://tile.openstreetmap.org/#Z/#X/#Y.png")
        self.osm.layer_add(osmgpsmap.GpsMapOsd(show_dpad=True, show_zoom=True))
        self.osm.connect('button_release_event', self._map_clicked)
#        self.osm.connect("motion_notify_event", self.update_distance)
        #connect keyboard shortcuts
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_FULLSCREEN, gtk.gdk.keyval_from_name("F11"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_UP, gtk.gdk.keyval_from_name("Up"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_DOWN, gtk.gdk.keyval_from_name("Down"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_LEFT, gtk.gdk.keyval_from_name("Left"))
        self.osm.set_keyboard_shortcut(osmgpsmap.KEY_RIGHT, gtk.gdk.keyval_from_name("Right"))
        self.vbox.pack_start(self.osm)
        self.status_bar = gtk.Statusbar()
        self.vbox.pack_start(self.status_bar, False, False, 0)
#        gobject.timeout_add(500, self.updateDistance)
        # create the track
        map_track = osmgpsmap.GpsMapTrack()
        map_track.set_property("line-width", 2)
        map_track.set_property("color", gtk.gdk.color_parse(color))
        for i in range(0, len(track.trackpoints)): 
            map_track.add_point(osmgpsmap.point_new_degrees(track.trackpoints.lats[i], 
                                                           track.trackpoints.lngs[i]))
        self.osm.track_add(map_track)
        # center the track
        (center_lat, lat_range) = track.get_mid_point_range("lats")
        (center_lng, lng_range) = track.get_mid_point_range("lngs")
        max_range = max(lat_range, lng_range)
        if max_range > 0.04: zoom = 14
        else: zoom = 15
        self.osm.set_center_and_zoom(latitude=center_lat, longitude=center_lng, zoom=zoom)
        # TODO: add numbers every 1/2 mile on the track. We'll need an image for each number to 
        # do this
        #        pb = gtk.gdk.pixbuf_new_from_file_at_size (num + ".png", 24, 24)
        #        self.osm.image_add(lat, lon, pb)
        self.set_title(title)

    def _map_clicked(self, osm, event):
        lat,lon = self.osm.get_event_location(event).get_degrees()
        if event.button == 1:
            self.status_bar.push(1, str(lat) + "," + str(lon))
            pass
        elif event.button == 2:
            self.osm.gps_add(lat, lon, heading=osmgpsmap.INVALID);
        elif event.button == 3:
            pb = gtk.gdk.pixbuf_new_from_file_at_size ("num.png", 24, 24)
            self.osm.image_add(lat, lon, pb)

    def _update_distance(self, osm, event):
        p = osmgpsmap.point_new_degrees(self.min_lat, self.min_lng)
        self.osm.convert_screen_to_geographic(int(event.x), int(event.y), p)
        self.status_bar.push(1, str(self.min_lat + p.rlat) + "," + str(self.min_lng + p.rlon))


if __name__ == "__main__":
    u = MapTracks()
    u.show_all()
    gtk.main()

