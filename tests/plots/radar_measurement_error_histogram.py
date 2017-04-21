########################################################
# Generates a histogram for buckets of 0-100 ft,
# 100-200 ft, 200-300 ft of the absolute error in x and y
# pos (units of meters) and speed x and y (units of meters/s)
# between radar data taken of a vehicle w.r.t. GPS
#
# Author: Patrick Emami
########################################################
import utm
import os
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt

from sensible.util import ops

RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
RADAR_POS_VAR = 1.3

RADAR_DIR = "C:\Users\pemami\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned radar"
GPS_DIR = "C:\Users\pemami\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned DSRC"

RADAR_TRACKS = ["AV_Track_ID_17_GPS_track_2.pkl", "AV_Track_ID_22_GPS_track_3.pkl", "AV_Track_ID_40_GPS_track_4.pkl",
                "AV_Track_ID_23_GPS_track_5.pkl", "AV_Track_ID_40_GPS_track_6.pkl", "AV_Track_ID_50_GPS_track_7.pkl"]

GPS_TRACKS = ["Test2.pkl", "Test3.pkl", "Test4.pkl", "Test5.pkl", "Test6.pkl", "Test7.pkl"]

if __name__ == '__main__':
    # load radar tracks
    radar_x = []
    radar_y = []
    #radar_lat = []
    #radar_lon = []
    df = ops.load_pkl(os.path.join(RADAR_DIR, RADAR_TRACKS[0]))
    # load GPS
    gps = ops.load_pkl(os.path.join(GPS_DIR, GPS_TRACKS[0]))

    y_offsets = df['x_Point1'].values
    x_offsets = df['y_Point1'].values

    gps_lat = gps['nfmlat'].values
    gps_lon = gps['nfmlon'].values

    # compute UTM coordinates of the radar
    x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

    for i in range(len(x_offsets)):
        radar_x.append(x + x_offsets[i])
        radar_y.append(y + y_offsets[i])
        lat, lon = utm.to_latlon(radar_x[i], radar_y[i], zone, letter)
        #print("{},{},{},{}".format(lat, lon, x_offsets[i], y_offsets[i]))
        #print("{},{}".format(lat, lon))

    for i in range(len(gps_lat)):
        print("{},{}".format(gps_lat[i], gps_lon[i]))
