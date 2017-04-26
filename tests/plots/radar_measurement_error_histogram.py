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
import argparse

from sensible.util import ops

RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
RADAR_POS_VAR = 1.3

RADAR_DIR = "C:\\Users\Patrick\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned radar"
GPS_DIR = "C:\\Users\Patrick\Dropbox (UFL)\Data\SW-42nd-SW-40-Radar-Installation\Cleaned DSRC"

RADAR_TRACKS = ["AV_Track_ID_26_GPS_track_2.pkl", "AV_Track_ID_22_GPS_track_3.pkl", "AV_Track_ID_45_GPS_track_4.pkl",
                "AV_Track_ID_32_GPS_track_5.pkl", "AV_Track_ID_40_GPS_track_6.pkl", "AV_Track_ID_50_GPS_track_7.pkl"]

GPS_TRACKS = ["Test2.pkl", "Test3.pkl", "Test4.pkl", "Test5.pkl", "Test6.pkl", "Test7.pkl"]

SUITCASE_TRACKS = ["suilog_1492107906.pkl", "suilog_1492108094.pkl", "suilog_1492108311.pkl",
                   "suilog_1492108557.pkl", "suilog_1492108779.pkl", "suilog_1492108956.pkl"]

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

SUITCASE_TS = [("2017-04-13 18:25:10.0", "2017-04-13 18:25:32.0"),
          ("2017-04-13 18:28:11.0", "2017-04-13 18:28:34.8"),
          ("2017-04-13 18:32:05.0", "2017-04-13 18:32:26.8"),
          ("2017-04-13 18:36:05.2", "2017-04-13 18:36:28.2"),
          ("2017-04-13 18:39:40.8", "2017-04-13 18:39:55.0"),
          ("2017-04-13 18:42:35.5", "2017-04-13 18:42:53.2")]

RADAR_RANGES = [(7, 177), (5, 228), (1, 219), (1, 231), (1, 143), (1, 175)]

GPS_RANGES = [(50, 220), (16, 239), (1, 219), (1, 231), (1, 143), (1, 175)]


def interpolate(r_df, r_idx, values):
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
    parser = argparse.ArgumentParser(description="Settings for re-computing data and generating plots")

    parser.add_argument('--preprocess-all', action='store_true', help='Preprocess and save data from radar, GPS, and suitcase')
    parser.add_argument('--preprocess-radar', action='store_true')
    parser.add_argument('--preprocess-gps', action='store_true')
    parser.add_argument('--preprocess-suitcase', action='store_true')
    parser.add_argument('--plot-histograms', action='store_true')
    parser.add_argument('--plot-utm', action='store_true')

    parser.set_defaults(preprocess_all=False)
    parser.set_defaults(preprocess_radar=False)
    parser.set_defaults(preprocess_gps=False)
    parser.set_defaults(preprocess_suitcase=False)
    parser.set_defaults(plot_histograms=False)
    parser.set_defaults(plot_utm=False)

    args = vars(parser.parse_args())

    # compute UTM coordinates of the radar
    x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

    if args['preprocess_all']:
        args['preprocess_radar'] = True
        args['preprocess_gps'] = True
        args['preprocess_suitcase'] = True

    if args['preprocess_radar'] or args['preprocess_gps'] or args['preprocess_suitcase']:
        radar_x = [[] for _ in range(len(GPS_TRACKS))]
        radar_y = [[] for _ in range(len(GPS_TRACKS))]
        radar_speed = [[] for _ in range(len(GPS_TRACKS))]

        gps_x = [[] for _ in range(len(GPS_TRACKS))]
        gps_y = [[] for _ in range(len(GPS_TRACKS))]

        suitcase_gps_x = [[] for _ in range(len(GPS_TRACKS))]
        suitcase_gps_y = [[] for _ in range(len(GPS_TRACKS))]
        suitcase_speed = [[] for _ in range(len(GPS_TRACKS))]
        suitcase_heading = [[] for _ in range(len(GPS_TRACKS))]

        for ii in range(len(GPS_TRACKS)):
            if args['preprocess_suitcase']:

                # Process suitcase data
                sc = ops.load_pkl(os.path.join(GPS_DIR, SUITCASE_TRACKS[ii]))
                sc_df = pd.DataFrame.from_dict(sc)

                # parse the datetime
                sc_df['time-stamp'] = pd.to_datetime(sc_df['time-stamp'], format="%Y-%m-%d %H:%M:%S:%f")
                sc_df = sc_df.set_index('time-stamp')
                idx_sc = pd.date_range(start=SUITCASE_TS[ii][0], end=SUITCASE_TS[ii][1], freq='50ms')

                interp_sc = interpolate(sc_df, idx_sc, ['lat', 'lon', 'heading', 'speed'])

                # downsample to 100ms
                interp_sc = interp_sc.resample('100ms', label='left').ffill()

                # extract GPS
                sc_gps_lat = interp_sc['lat'].values
                sc_gps_lon = interp_sc['lon'].values
                sc_gps_heading = interp_sc['heading'].values
                sc_gps_speed = -1. * interp_sc['speed'].values

                # compute GPS tracks in UTM
                for i in range(GPS_RANGES[ii][0], GPS_RANGES[ii][1]):
                    sx, sy, _, _ = utm.from_latlon(sc_gps_lat[i], sc_gps_lon[i])
                    suitcase_gps_x[ii].append(sx)
                    suitcase_gps_y[ii].append(sy)
                    suitcase_speed[ii].append(sc_gps_speed[i])
                    suitcase_heading[ii].append(sc_gps_heading[i])

            if args['preprocess_radar']:
                # load radar tracks
                df = ops.load_pkl(os.path.join(RADAR_DIR, RADAR_TRACKS[ii]))
                #df.to_csv(os.path.join(RADAR_DIR, "AV_Track_ID_45_solo_GPS_track_4.csv"))

                # parse the datetime
                df['Time_s'] = pd.to_datetime(df['Time_s'], format="%H:%M:%S:%f")
                df = df.set_index('Time_s')
                idx_r = pd.date_range(start=RADAR_TS[ii][0], end=RADAR_TS[ii][1], freq='50ms')

                interp_r = interpolate(df, idx_r, ['x_Point1', 'y_Point1', 'Speed_x', 'Speed_y'])

                # downsample to 100ms
                interp_r = interp_r.resample('100ms', label='left').ffill()

                # coordinate transform
                y_offsets = interp_r['x_Point1'].values
                x_offsets = -interp_r['y_Point1'].values
                speed_x = interp_r['Speed_x'].values

                # compute radar tracks in UTM coordinates
                for i in range(RADAR_RANGES[ii][0], RADAR_RANGES[ii][1]):
                    radar_x[ii].append(x + x_offsets[i])
                    radar_y[ii].append(y + y_offsets[i])
                    radar_speed[ii].append(speed_x[i])

                    lat, lon = utm.to_latlon(radar_x[ii][-1], radar_y[ii][-1], zone, letter)
                    # print("{},{},{},{}".format(lat, lon, x_offsets[i], y_offsets[i]))
                    # print("{},{}".format(lat, lon))

            if args['preprocess_gps']:
                # Pre-process GPS data from the Novatel
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

                interp_gps = interpolate(gps, idx_g, ['nfmlat', 'nfmlon', 'nfmposvar'])

                # extract GPS
                gps_lat = interp_gps['nfmlat'].values
                gps_lon = interp_gps['nfmlon'].values

                # compute GPS tracks in UTM
                for i in range(GPS_RANGES[ii][0], GPS_RANGES[ii][1]):
                    gx, gy, _, _ = utm.from_latlon(gps_lat[i], gps_lon[i])
                    gps_x[ii].append(gx)
                    gps_y[ii].append(gy)

        if args['preprocess_suitcase']:
            ops.dump(suitcase_gps_x, 'suitcase_gps_x.pkl')
            ops.dump(suitcase_gps_y, 'suitcase_gps_y.pkl')
            ops.dump(suitcase_speed, 'suitcase_speed.pkl')
            ops.dump(suitcase_heading, 'suitcase_heading.pkl')
        if args['preprocess_radar']:
            ops.dump(radar_x, 'radar_x.pkl')
            ops.dump(radar_y, 'radar_y.pkl')
            ops.dump(radar_speed, 'radar_speed.pkl')
        if args['preprocess_gps']:
            ops.dump(gps_x, 'gps_x.pkl')
            ops.dump(gps_y, 'gps_y.pkl')

    if args['plot_utm']:
        RUN = 0
        gps_x = ops.load_pkl('gps_x.pkl')
        gps_y = ops.load_pkl('gps_y.pkl')
        sc_gps_x = ops.load_pkl('suitcase_gps_x.pkl')
        sc_gps_y = ops.load_pkl('suitcase_gps_y.pkl')

        plt.scatter(gps_x[RUN], gps_y[RUN], c='r')
        plt.scatter(sc_gps_x[RUN], sc_gps_y[RUN], c='b')
        plt.show()

    if args['plot_histograms']:
        radar_y = ops.load_pkl('radar_y.pkl')
        gps_y = ops.load_pkl('gps_y.pkl')
        suitcase_y = ops.load_pkl('suitcase_gps_y.pkl')

        radar_x = ops.load_pkl('radar_x.pkl')
        gps_x = ops.load_pkl('gps_x.pkl')
        suitcase_x = ops.load_pkl('suitcase_gps_x.pkl')

        radar_speed = ops.load_pkl('radar_speed.pkl')
        suitcase_speed = ops.load_pkl('suitcase_speed.pkl')
        suitcase_heading = ops.load_pkl('suitcase_heading.pkl')

        errs_y = []
        errs_x = []
        errs_hp_radar_range_all = []
        errs_lp_radar_range_all = []
        errs_lp_radar_speed_all = []

        track_2_start = 27
        track_7_start = 10
        for ii in range(len(GPS_TRACKS)):
            if ii == 1:
                start = track_2_start
            elif ii == 5:
                start = track_7_start
            else:
                start = 0
            idx_y = 0

            # diff in range
            for y1, y2 in zip(suitcase_y[ii], gps_y[ii]):
                if idx_y < start:
                    idx_y += 1
                    continue

                errs_y.append(y2 - y1)
                idx_y += 1

            idx_x = 0
            # diff in range
            for x1, x2 in zip(suitcase_x[ii], gps_x[ii]):
                if idx_x < start:
                    idx_x += 1
                    continue
                errs_x.append(x2 - x1)
                idx_x += 1

            # compare ranges of HP gps and radar for all tracks
            for y1, y2 in zip(gps_y[ii], radar_y[ii]):
                errs_hp_radar_range_all.append(y1 - y2)

            idx = 0
            for y1, y2 in zip(suitcase_y[ii], radar_y[ii]):
                if idx < start:
                    idx += 1
                    continue
                errs_lp_radar_range_all.append(y1 - y2)
                idx += 1

            for j in range(start, len(suitcase_speed[ii])):
                errs_lp_radar_speed_all.append(-suitcase_speed[ii][j] - radar_speed[ii][j])

            plt.scatter(range(len(suitcase_speed[ii][start:])), suitcase_speed[ii][start:], c='r', label='suitcase')
            plt.scatter(range(len(radar_speed[ii][start:])), radar_speed[ii][start:], c='b', label='radar')
            plt.show()

        # fig, axarr = plt.subplots(2, sharex=False)
        # axarr[0].hist(errs_y, bins=15)
        # axarr[0].set_title('High-precision vs Low-precision GPS relative error in UTM northing')
        # axarr[1].hist(errs_x, bins=15)
        # axarr[1].set_title('High-precision vs Low-precision GPS relative error in UTM easting')

        # plt.show()

        # plt.hist(errs_hp_radar_range_all, bins=25)
        # plt.show()

        # plt.hist(errs_lp_radar_range_all, bins=25)
        # plt.show()
        # plt.hist(errs_lp_radar_speed_all, bins=20)
        # plt.show()