#!/usr/bin/python

import os
import time

f = open("garmin-activity-links", "r")
for line in f:
    if line.startswith("http"): 
        activity = int(line.split("/")[4])
        print activity
        os.system("firefox http://connect.garmin.com/proxy/activity-service-1.0/tcx/activity/" + str(activity) + "?full=true")
        time.sleep(10)
f.close()



