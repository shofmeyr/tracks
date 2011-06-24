import sys
import os
import numpy
import shutil
from track import Track

class GoogleEarth:
    @classmethod
    def show_in_google_earth(cls, track):
        (center_lat, lat_range) = track.get_mid_point_range("lats")
        (center_lng, lng_range) = track.get_mid_point_range("lngs")
        max_alt = max(track.trackpoints.gps_elevs) + 1000
        min_hr = 120.0
        max_hr = 180.0
        num_hr_colors = 20
        fname = "/tmp/" + track.get_start_time_as_str() + ".kml"
        f = open(fname, "w+")
        print>>f, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        print>>f, "<kml xmlns=\"http://www.opengis.net/kml/2.2\">"
        print>>f, "  <Document>"
        print>>f, "    <name>Track " + track.get_start_time_as_str() + "</name>"
        print>>f, "    <gx:FlyTo>"
        print>>f, "      <gx:duration>0.1</gx:duration>"
        print>>f, "      <gx:flyToMode>smooth</gx:flyToMode>"
        print>>f, "        <Camera>"
        print>>f, "          <longitude>" + str(center_lng) + "</longitude>"
        print>>f, "          <latitude>" + str(center_lat) + "</latitude>"
        print>>f, "          <altitude>" + str(max_alt) + "</altitude>"
        print>>f, "          <tilt>33</tilt>"
        print>>f, "        </Camera>"
        print>>f, "    </gx:FlyTo>"
        print>>f, "    <ScreenOverlay id=\"khScreenOverlay756\">"
        print>>f, "      <Icon><href>hr-legend.png</href></Icon>"
        print>>f, "      <overlayXY x=\"0\" y=\"0\" xunits=\"fraction\" yunits=\"fraction\"/>"
        print>>f, "      <screenXY x=\"0\" y=\"30\" xunits=\"pixels\" yunits=\"pixels\"/>"
        print>>f, "      <size x=\"60\" y=\"220\" xunits=\"pixels\" yunits=\"pixels\"/>"
        print>>f, "    </ScreenOverlay>"
        
        for i in range(0, num_hr_colors):
            color_hr = float(i) * (max_hr - min_hr) / float(num_hr_colors) + min_hr
#            print i, color_hr, GoogleEarth.data_point_to_color(color_hr, min_hr, max_hr)
            print>>f, "    <Style id=\"color" + str(i) + "\">"
            print>>f, "      <LineStyle>"
            print>>f, "        <color>ff" + GoogleEarth.data_point_to_color(color_hr, min_hr, max_hr) + "</color>"
            print>>f, "        <width>6</width>"
            print>>f, "      </LineStyle>"
            print>>f, "    </Style>"

        for i in range(0, len(track.trackpoints), 5):
            av_hr = numpy.average(track.trackpoints.hrs[i:i+5])
            color_num = int(float(num_hr_colors) * (av_hr - min_hr) / (max_hr - min_hr)) 
            if color_num < 0: color_num = 0
            if color_num >= num_hr_colors: color_num = num_hr_colors - 1
            print>>f, "    <Placemark>"
            print>>f, "      <name>Absolute Extruded</name>"
            print>>f, "      <styleUrl>#color" + str(color_num) + "</styleUrl>"
            print>>f, "      <LineString>"
            print>>f, "        <altitudeMode>clampToGround</altitudeMode>"
            print>>f, "        <coordinates>"
            for t in range(i, i + 6):
                if t >= len(track.trackpoints.lngs): break
                print>>f, "          " + str(track.trackpoints.lngs[t]) + "," + str(track.trackpoints.lats[t])
            print>>f, "        </coordinates>"
            print>>f, "      </LineString>"
            print>>f, "    </Placemark>"

        print>>f, "  </Document>"
        print>>f, "</kml>"
        f.close()
        shutil.copy("hr-legend.png", "/tmp/hr-legend.png")
        os.spawnlp(os.P_NOWAIT, "google-earth", "google-earth", fname)

    @classmethod
    def data_point_to_color(cls, val, min_val, max_val):
        GAMMA = 0.8
        INTENSITY_MAX = 255.0
        num_spectrum_colors = 5
        num_bits = 255
        if val >= max_val: val = max_val
        if val <= min_val: val = min_val
        spectrum_color = float(num_spectrum_colors) * (float(val) - min_val) / (max_val - min_val) + 0.25
        if spectrum_color < 1: rgb = (1.0 - spectrum_color, 0, 1)
        elif spectrum_color < 2: rgb = (0, spectrum_color - 1.0, 1)
        elif spectrum_color < 3: rgb = (0, 1, 3.0 - spectrum_color)
        elif spectrum_color < 4: rgb = (spectrum_color - 3.0, 1, 0)
        else: rgb = (1, 5.0 - spectrum_color, 0)

        if spectrum_color < 1.5: factor = 0.5 + (spectrum_color / 3.0)
        else: factor = 1.0
        color = ""
        for x in rgb: 
            try:
                if x != 0: x = round(INTENSITY_MAX * ((x * factor) ** GAMMA))
            except ValueError as e:
                print e
                print rgb, factor, val
                x = 0
            color += "%02x" % x
       # for some reason google expects the colors as BGR, so we reverse the string here
        return color[::-1]


    @classmethod
    def data_point_to_color2(cls, val, min_val, max_val):
        MIN_VISIBLE_WAVE_LEN = 380.0
        MAX_VISIBLE_WAVE_LEN = 780.0
        GAMMA = 0.8
        INTENSITY_MAX = 255.0

        wave_len = (val - min_val) / (max_val - min_val) * \
            (MAX_VISIBLE_WAVE_LEN - MIN_VISIBLE_WAVE_LEN) + MIN_VISIBLE_WAVE_LEN
        if wave_len <= 419: factor = 0.5 + 0.5 * (wave_len - 380) / (420 - 380)
        elif wave_len >= 420 and wave_len <= 700:  factor = 1.0
        elif wave_len >= 701 and wave_len <= 780:  factor = 0.5 + 0.5 * (780 - wave_len) / (780 - 700)
        else: factor = 0.0
        if wave_len <= 439: rgb = (-(wave_len - 440) / (440 - 380), 0.0, 1.0) #violet
        elif wave_len <= 489: rgb = (0.0, (wave_len - 440) / (490 - 440), 1.0) #blue
        elif wave_len <= 509: rgb = (0.0, 1.0, -(wave_len - 510) / (510 - 490)) #green
        elif wave_len <= 579: rgb = ((wave_len - 510) / (580 - 510), 1.0, 0) #yellow
        elif wave_len <= 644: rgb = (1.0, -(wave_len - 645) / (645 - 580), 0) #orange
        elif wave_len <= 780: rgb = (1.0, 0.0, 0.0) #red
        else: rgb = (0.0, 0.0, 0.0)
        color = ""
        for x in rgb: 
            try:
                if x != 0: x = round(INTENSITY_MAX * ((x * factor) ** GAMMA))
            except ValueError as e:
                print e
                print rgb, factor, wave_len
                x = 0
            color += "%02x" % x
        # for some reason google expects the colors as BGR, so we reverse the string here
        return color[::-1]
            

