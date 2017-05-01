#import matplotlib
#matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import sensible.util.ops as ops
import utm
import numpy as np


N_TRACKS = 6
RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
# compute UTM coordinates of the radar
x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

if __name__ == '__main__':
    radar_y = ops.load_pkl('radar_y.pkl')
    gps_y = ops.load_pkl('gps_y.pkl')
    suitcase_y = ops.load_pkl('suitcase_gps_y.pkl')
    radar_speed = ops.load_pkl('radar_speed.pkl')

    track_2_start = 27
    track_7_start = 10

    errs_hp_radar_range_all = []
    errs_y = []

    for ii in range(N_TRACKS):

        for j in range(len(radar_y[ii])):
            radar_y[ii][j] -= y
            gps_y[ii][j] -= y
            suitcase_y[ii][j] -= y
            suitcase_y[ii][j] -= 3.6576

        if ii == 1:
            start = track_2_start
        elif ii == 5:
            start = track_7_start
        else:
            start = 0

        idx_y = 0
        # Suitcase vs HP GPS northing error
        for y1, y2 in zip(suitcase_y[ii], gps_y[ii]):
            if idx_y < start:
                idx_y += 1
                continue

            errs_y.append(y2 - y1)
            idx_y += 1

        # compare range of HP GPS and radar for all tracks
        errs_hp_radar_start = len(errs_hp_radar_range_all)
        for y1, y2 in zip(gps_y[ii], radar_y[ii]):
            errs_hp_radar_range_all.append(y1 - y2)

    sample_mu = np.mean(errs_hp_radar_range_all, axis=0)
    sample_var = np.var(errs_hp_radar_range_all, axis=0, ddof=1)

    lp_sample_mu = np.mean(errs_y, axis=0)
    lp_sample_var = np.var(errs_y, axis=0, ddof=1)

    print('HP vs radar range\n')
    print('mu: ', sample_mu)
    print('var: ', sample_var)

    print('LP vs HP range\n')
    print('mu: ', lp_sample_mu)
    print('var: ', lp_sample_var)
