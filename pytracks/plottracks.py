#from matplotlib.figure import Figure
#import matplotlib.font_manager as font_manager
#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar
#import matplotlib.pyplot as pyplot


        # fig = Figure()
        # ax = fig.add_subplot(111)
        # minElev = 300000
        # maxElev = 0
        # maxDist = 0
        # try: 
        #     trackDate = datetime.datetime.strptime(options.plotMap, "%Y-%m-%d-%H%M%S")
        #     trackDates.append(options.plotMap)
        #     title = "Track " + options.plotMap
        # except ValueError: 
        #     print>>sys.stderr, "No tracks found with trackpoints"
        #     sys.exit(0)
        # if not mapTracks.addTracks(tracks, trackDates, colors):
        #     print>>sys.stderr, "No tracks found with trackpoints"
        #     sys.exit(0)

        
        #             if not maptracks.addTrack(track.trackpoints.getLats(), track.trackpoints.getLngs(), color = colors[i]):
        #                 print>>sys.stderr, "Track", track.startTime, "is empty"
        #             else:
        #                 (gpsElevChange, mapElevChange) = track.trackpoints.getElevChanges()
        #                 ax.plot(track.trackpoints.getDists(), track.trackpoints.getMapElevs(), 
        #                         label = track.getDate() + " (" + ("%.0f" % mapElevChange) + ")", color = colors[i])
        #             (trackMinElev, trackMaxElev) = track.trackpoints.getMinMaxElevs(options.useGps)
        #             if maxElev < trackMaxElev: maxElev = trackMaxElev
        #             if minElev > trackMinElev: minElev = trackMinElev
        #             if maxDist < track.dist: maxDist = track.dist
        #             found = True
        #             i += 1
        #             if i == len(colors): i = 0
        #             if trackDate != None: 
        #                 title += ":  %.0f miles" % track.dist + " %.0f feet" % track.getElevChange(options.useGps)
        #                 break
        # if not found:
        #     if trackDate != None: print>>sys.stderr, "*** ERROR: No tracks for", options.plotMap, "with trackpoints ***"
        #     sys.exit(0)
        # ax.legend(loc = "lower right", prop = font_manager.FontProperties(size = "x-small"))
        # ax.axis([0, maxDist, minElev - 200, maxElev])
        # ax.get_axes().set_xlabel("Distance (miles)")
        # ax.get_axes().set_ylabel("Elevation (ft)")
        # ax.get_axes().grid()
        # canvas = FigureCanvas(fig)  
        # vbox.pack_start(canvas)
        # toolbar = NavigationToolbar(canvas, win)
        # vbox.pack_start(toolbar, False, False)


        # title = "Track "
        # datetime.datetime.strptime(options.plotMap, "%Y-%m-%d-%H%M%S")

#        win.set_title("Elevation profile, " + title)
#        win.show_all()
