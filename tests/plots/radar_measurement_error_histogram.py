########################################################
# Generates a histogram for buckets of 0-100 m,
# 100-200 m, 200-300 m of the absolute error in x and y
# pos (units of meters) and speed x and y (units of meters/s)
# between radar data taken of a vehicle w.r.t. GPS
#
# Author: Patrick Emami
########################################################
import utm
import os
#import matplotlib
#matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from sensible.util import ops

RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
RADAR_POS_VAR = 1.3

RADAR_DIR = "C:\\Users\Patrick\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned radar"
GPS_DIR = "C:\\Users\Patrick\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned DSRC"

RADAR_TRACKS = ["AV_Track_ID_26_GPS_track_2.pkl", "AV_Track_ID_22_GPS_track_3.pkl", "AV_Track_ID_45_GPS_track_4.pkl",
                "AV_Track_ID_32_GPS_track_5.pkl", "AV_Track_ID_40_GPS_track_6.pkl", "AV_Track_ID_50_GPS_track_7.pkl"]

GPS_TRACKS = ["Test2.pkl", "Test3.pkl", "Test4.pkl", "Test5.pkl", "Test6.pkl", "Test7.pkl"]

RADAR_TS = [("1900-01-01 03:32:39.0", "1900-01-01 03:32:57.0"),
            ("1900-01-01 03:35:36.5", "1900-01-01 03:35:59.5"),
            ("1900-01-01 03:39:29.5", "1900-01-01 03:39:51.4"),
            ("1900-01-01 03:43:29.9", "1900-01-01 03:43:53.0"),
            ("1900-01-01 03:47:05.3", "1900-01-01 03:47:19.6"),
            ("1900-01-01 03:50:00.0", "1900-01-01 03:50:17.4")]

GPS_TS = [("1900-01-01 18:25:10.0", "1900-01-01 18:25:32.0"),
          ("1900-01-01 18:28:11.0", "1900-01-01 18:28:34.8"),
          ("1900-01-01 18:32:05.0", "1900-01-01 18:32:26.8"),
          ("1900-01-01 18:36:05.2", "1900-01-01 18:36:28.2"),
          ("1900-01-01 18:39:40.8", "1900-01-01 18:39:55.0"),
          ("1900-01-01 18:42:35.5", "1900-01-01 18:42:53.2")]

RADAR_RANGES = [(7, 177), (5, 228), (1, 219), (1, 231), (1, 143), (1, 175)]

GPS_RANGES = [(50, 220), (16, 239), (1, 219), (1, 231), (1, 143), (1, 175)]


def interpolate_fields(r_df, r_idx, values):
    rs = pd.DataFrame(index=r_idx)
    idx_after = np.searchsorted(r_df.index.values, rs.index.values)

    for v in values:
        rs['after'] = r_df.loc[r_df.index[idx_after], v].values
        rs['before'] = r_df.loc[r_df.index[idx_after - 1], v].values
        rs['after_time'] = r_df.index[idx_after]
        rs['before_time'] = r_df.index[idx_after - 1]

        # calculate new weighted value
        rs['span'] = (rs['after_time'] - rs['before_time'])
        rs['after_weight'] = (rs['after_time'] - rs.index) / rs['span']
        # I got errors here unless I turn the index to a series
        rs['before_weight'] = (pd.Series(data=rs.index, index=rs.index) - rs['before_time']) / rs['span']

        rs[v] = rs.eval('before * before_weight + after * after_weight')
    return rs

if __name__ == '__main__':
    radar_x = [[] for _ in range(len(GPS_TRACKS))]
    radar_y = [[] for _ in range(len(GPS_TRACKS))]
    gps_x = [[] for _ in range(len(GPS_TRACKS))]
    gps_y = [[] for _ in range(len(GPS_TRACKS))]
    errs_ = [[] for _ in range(len(GPS_TRACKS))]

    for ii in range(5, len(GPS_TRACKS)):
        # load radar tracks
        df = ops.load_pkl(os.path.join(RADAR_DIR, RADAR_TRACKS[ii]))
        #df.to_csv(os.path.join(RADAR_DIR, "AV_Track_ID_45_solo_GPS_track_4.csv"))

        # parse the datetime
        df['Time_s'] = pd.to_datetime(df['Time_s'], format="%H:%M:%S:%f")
        df = df.set_index('Time_s')
        idx_r = pd.date_range(start=RADAR_TS[ii][0], end=RADAR_TS[ii][1], freq='50ms')

        interp_r = interpolate_fields(df, idx_r, ['x_Point1', 'y_Point1', 'Speed_x', 'Speed_y'])

        # downsample to 100ms
        interp_r = interp_r.resample('100ms', label='left').ffill()

        # load GPS
        gps = ops.load_pkl(os.path.join(GPS_DIR, GPS_TRACKS[ii]))

        # add MS to the utctime
        gps_utctime_vals = gps['utctime'].values.astype(np.float64)
        start = gps_utctime_vals[0]
        current = start
        t = 0.0
        t_delta = 0.1
        for i in range(len(gps_utctime_vals)):
            if gps_utctime_vals[i] != current:
                t = 0.0
                current = gps_utctime_vals[i]
            gps_utctime_vals[i] += t
            t += t_delta

        gps['utctime'] = pd.DataFrame(gps_utctime_vals)
        # parse the datetime
        gps['utctime'] = pd.to_datetime(gps['utctime'], format="%H%M%S.%f")
        # extend gps time by adding time increments of 50 ms
        gps = gps.set_index('utctime')
        idx_g = pd.date_range(start=GPS_TS[ii][0], end=GPS_TS[ii][1], freq='100ms')

        interp_gps = interpolate_fields(gps, idx_g, ['nfmlat', 'nfmlon', 'nfmposvar'])

        # coordinate transform
        y_offsets = interp_r['x_Point1'].values
        x_offsets = -interp_r['y_Point1'].values

        # extract GPS
        gps_lat = interp_gps['nfmlat'].values
        gps_lon = interp_gps['nfmlon'].values

        # compute UTM coordinates of the radar
        x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

        # compute radar tracks in UTM coordinates
        for i in range(RADAR_RANGES[ii][0], RADAR_RANGES[ii][1]):
            radar_x[ii].append(x + x_offsets[i])
            radar_y[ii].append(y + y_offsets[i])
            lat, lon = utm.to_latlon(radar_x[ii][-1], radar_y[ii][-1], zone, letter)
            #print("{},{},{},{}".format(lat, lon, x_offsets[i], y_offsets[i]))
            #print("{},{}".format(lat, lon))

        # compute GPS tracks in UTM
        for i in range(GPS_RANGES[ii][0], GPS_RANGES[ii][1]):
            gx, gy, _, _ = utm.from_latlon(gps_lat[i], gps_lon[i])
            gps_x[ii].append(gx)
            gps_y[ii].append(gy)

        # plt.scatter(upsampled_utm_x_series, upsampled_utm_y_series, c='r')
        # plt.scatter(gps_x[ii], gps_y[ii], c='r')
        # plt.scatter(radar_x[ii], radar_y[ii], c='b')
        # plt.show()

        errs_[ii] = [[] for _ in range(3)]

        idx = RADAR_RANGES[ii][0]
        for y1, y2 in zip(radar_y[ii], gps_y[ii]):
            if 200. < y_offsets[idx] <= 300:
                errs_[ii][2].append(abs(y1 - y2))
            elif 100. < y_offsets[idx] <= 200:
                errs_[ii][1].append(abs(y1 - y2))
            elif 0. < y_offsets[idx] <= 100:
                errs_[ii][0].append(abs(y1 - y2))
            idx += 1

        fig, axarr = plt.subplots(3, sharex=True)
        axarr[0].hist(errs_[ii][0], bins=15)
        axarr[0].set_title('0 < y <= 100 m')
        axarr[1].hist(errs_[ii][1], bins=15)
        axarr[1].set_title('100 < y <= 200 m')
        axarr[2].hist(errs_[ii][2], bins=15)
        axarr[2].set_title('200 < y <= 300 m')

        plt.show()



