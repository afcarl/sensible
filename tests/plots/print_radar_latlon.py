import os
import sys
import sensible.util.ops as ops
#import matplotlib
#matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import utm
import pandas as pd


RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591

#RADAR_DIR = "C:\\Users\Patrick\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned radar"
GPS_DIR = "C:\Users\pemami\Workspace\Github\sensible\\tests\data\SW-42-SW-40\\"

#RADAR_TRACKS = ["AV_Track_ID_26_GPS_track_2.pkl", "AV_Track_ID_22_GPS_track_3.pkl", "AV_Track_ID_45_GPS_track_4.pkl",
#                "AV_Track_ID_32_GPS_track_5.pkl", "AV_Track_ID_40_GPS_track_6.pkl", "AV_Track_ID_50_GPS_track_7.pkl"]

#GPS_TRACKS = ["Test2.pkl", "Test3.pkl", "Test4.pkl", "Test5.pkl", "Test6.pkl", "Test7.pkl"]

SUITCASE_TRACKS = ["dsrc_truck_1_20170502.pkl"]

if __name__ == '__main__':

    #i = int(sys.argv[1])
    i = 0
    radar_x = []
    radar_y = []
    gps_x = []
    gps_y = []
    suitcase_x = []
    suitcase_y = []

    # load radar tracks
    df = ops.load_pkl(os.path.join(GPS_DIR, "radar_truck_1_20170502_objID_3.pkl"))
    # #df.to_csv(RADAR_DIR + "\AV_Track_ID_50_solo_GPS_track_7.csv")
    #
    # # load GPS
    # gps = ops.load_pkl(os.path.join(GPS_DIR, GPS_TRACKS[i]))

    # load suitcase
    sc = pd.DataFrame.from_dict(ops.load_pkl(os.path.join(GPS_DIR, SUITCASE_TRACKS[i])))

    # coordinate transform
    y_offsets = df['x_Point1'].values
    x_offsets = -df['y_Point1'].values
    #
    # # extract GPS
    # gps_lat = gps['nfmlat'].values
    # gps_lon = gps['nfmlon'].values

    sc_lat = sc['lat'].values
    sc_lon = sc['lon'].values

    # compute UTM coordinates of the radar
    x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)
    ts = df['Time_s'].values

    #compute radar tracks in UTM coordinates
    for i in range(len(x_offsets)):
        radar_x.append(x + x_offsets[i])
        radar_y.append(y + y_offsets[i])
        lat, lon = utm.to_latlon(radar_x[-1], radar_y[-1], zone, letter)
        #print("{},{}".format(lat, lon))
        print("{},{},{}".format(lat, lon, ts[i]))
    #
    # print('GPS: \n')
    # # compute GPS tracks in UTM
    # for i in range(len(gps_lat)):
    #     gx, gy, _, _ = utm.from_latlon(gps_lat[i], gps_lon[i])
    #     gps_x.append(gx)
    #     gps_y.append(gy)
    #     print("{},{},{}".format(gps_lat[i], gps_lon[i], i))

    print('SC: \n')
    h = sc['h'].values
    m = sc['m'].values
    s = sc['s'].values
    # compute GPS tracks in UTM
    for i in range(len(sc_lat)):
        sx, sy, _, _ = utm.from_latlon(sc_lat[i], sc_lon[i])
        suitcase_x.append(sx)
        suitcase_y.append(sy)
        print("{},{},{}:{}:{}".format(sc_lat[i], sc_lon[i], h[i], m[i], s[i]))

    # plt.scatter(gps_x, gps_y, c='r')
    # plt.scatter(radar_x, radar_y, c='b')
    # plt.scatter(suitcase_x, suitcase_y, c='y')
    # plt.show()

