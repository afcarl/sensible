#import matplotlib
#matplotlib.use('Qt4Agg')

import matplotlib.pyplot as plt
import ops as ops
import utm
import numpy as np
import os
import matplotlib.pyplot as plt

# N_TRACKS = 6
# RADAR_LAT = 29.6216931
# RADAR_LON = -82.3867591
# # compute UTM coordinates of the radar
# x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)
data_dir = 'SW-16-SW-13'

if __name__ == '__main__':
    # radar_y = ops.load_pkl(os.path.join(data_dir, 'radar_y.pkl'))
    # radar_x = ops.load_pkl(os.path.join(data_dir, 'radar_x.pkl'))
    # gps_y = ops.load_pkl(os.path.join(data_dir, 'gps_y.pkl'))
    # gps_x = ops.load_pkl(os.path.join(data_dir, 'gps_x.pkl'))
    # suitcase_y = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_y.pkl'))
    # suitcase_x = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_x.pkl'))
    # radar_speed = ops.load_pkl(os.path.join(data_dir, 'radar_speed.pkl'))
    # suitcase_speed = ops.load_pkl(os.path.join(data_dir, 'suitcase_speed.pkl'))
    #
    # track_2_start = 27
    # track_7_start = 10
    #
    # errs_hp_radar_range_all = []
    # errs_y = []
    #
    # errs_x = []
    # errs_x_abs = []
    # errs_hp_radar_lat_all = []
    # errs_lp_radar_lat_all = []
    # errs_lp_radar_speed_all = []
    #
    # for ii in range(N_TRACKS):
    #
    #     for j in range(len(radar_y[ii])):
    #         radar_y[ii][j] -= y
    #         gps_y[ii][j] -= y
    #         suitcase_y[ii][j] -= y
    #         #suitcase_y[ii][j] -= 3.6576
    #
    #     for j in range(len(radar_x[ii])):
    #         radar_x[ii][j] -= x
    #         gps_x[ii][j] -= x
    #         suitcase_x[ii][j] -= x
    #
    #     if ii == 1:
    #         start = track_2_start
    #     elif ii == 5:
    #         start = track_7_start
    #     else:
    #         start = 0
    #
    #     idx_y = 0
    #     # Suitcase vs HP GPS northing error
    #     for y1, y2 in zip(suitcase_y[ii], gps_y[ii]):
    #         if idx_y < start:
    #             idx_y += 1
    #             continue
    #
    #         errs_y.append(y2 - y1)
    #         idx_y += 1
    #
    #     # compare range of HP GPS and radar for all tracks
    #     errs_hp_radar_start = len(errs_hp_radar_range_all)
    #     for y1, y2 in zip(gps_y[ii], radar_y[ii]):
    #         errs_hp_radar_range_all.append(y1 - y2)
    #
    #     errs_x_start_idx = len(errs_x)
    #     idx_x = 0
    #     # Suitcase vs HP GPS easting error
    #     for x1, x2 in zip(suitcase_x[ii], gps_x[ii]):
    #         if idx_x < start:
    #             idx_x += 1
    #             continue
    #
    #         errs_x.append(x2 - x1)
    #         errs_x_abs.append(abs(x2 - x1))
    #         idx_x += 1
    #
    #     # compare range of HP GPS and radar for all tracks
    #     idx = 0
    #     for x1, x2 in zip(gps_x[ii], radar_x[ii]):
    #         errs_hp_radar_lat_all.append(x1 - x2)
    #         idx += 1
    #
    #     for j in range(start, len(suitcase_speed[ii])):
    #         errs_lp_radar_speed_all.append(suitcase_speed[ii][j] - radar_speed[ii][j])

    # sample_mu = np.mean(errs_hp_radar_range_all, axis=0)
    # sample_var = np.var(errs_hp_radar_range_all, axis=0, ddof=1)

    errs_y = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_y_errors.pkl'))
    errs_x = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_x_errors.pkl'))
    errs_heading = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_heading_errors.pkl'))

    lp_sample_mu = np.mean(errs_y, axis=0)
    lp_sample_var = np.var(errs_y, axis=0, ddof=1)
    lp_sample_std = np.std(errs_y, ddof=1)

    lp_heading_sample_mu = np.mean(errs_heading, axis=0)
    lp_heading_sample_var = np.var(errs_heading, axis=0, ddof=1)

    # lat_hp_radar_mu = np.mean(errs_hp_radar_lat_all, axis=0)
    # lat_hp_radar_var = np.var(errs_hp_radar_lat_all, axis=0, ddof=1)

    lat_lp_sample_mu = np.mean(errs_x, axis=0)
    lat_lp_sample_var = np.var(errs_x, axis=0, ddof=1)
    lat_lp_sample_std = np.std(errs_x, ddof=1)

    # speed_lp_sample_mu = np.mean(errs_lp_radar_speed_all, axis=0)
    # speed_lp_sample_var = np.var(errs_lp_radar_speed_all, axis=0, ddof=1)

    # print('HP vs radar range')
    # print('mu: ', sample_mu)
    # print('var: ', sample_var)

    print('\nLP vs HP range')
    print('mu: ', lp_sample_mu)
    print('2-std: ', 2*lp_sample_std)

    print('\nLP vs HP heading')
    print('mu: ', lp_heading_sample_mu)
    print('var: ', lp_heading_sample_var)

    # print('\nHP vs radar lat')
    # print('mu: ', lat_hp_radar_mu)
    # print('var: ', lat_hp_radar_var)

    print('\nLP vs HP lat')
    print('mu: ', lat_lp_sample_mu)
    print('2-std: ', 2*lat_lp_sample_std)
    #
    # print('\nLP vs radar speed')
    # print('mu: ', speed_lp_sample_mu)
    # print('var: ', speed_lp_sample_var)

    #Gaussian measurement noise
    N = 500
    true_north = 90
    x = 240
    theta = np.deg2rad(x + true_north)

    cov = np.array([[lp_sample_var , 0],[0, lat_lp_sample_var]])
    #H = np.array([np.cos(theta), np.sin(theta)])
    #cov = cov * H
    rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    cov = np.matmul(np.matmul(rot, cov), rot.T)
    print('cov: {}'.format(cov))
    fig = plt.figure()
    for i in range(N):
        s = np.random.multivariate_normal(np.zeros(2), cov)
        plt.scatter(s[0], s[1])
    
    plt.xlim(-5, 5)
    plt.ylim(-5, 5)
#    plt.show()

    # bias estimate is rot(180) * [max(0.167 * x_dot (m/s) , 3), max(0.167 * y_dot (m/s) , 3)]
    # rot = np.array([[np.cos(np.pi), -np.sin(np.pi)], [np.sin(np.pi), np.cos(np.pi)]])
    # vv = np.linspace(0, 20, 40)
    # yy = []
    # for v in vv:
    #     theta = np.deg2rad(88) % np.pi
    #     x = np.array([min(0.167 * v * np.cos(theta), 3), min(0.167 * v * np.sin(theta), 3)])
    #     x = np.matmul(rot, x)
    #     yy.append(x)
    #     plt.scatter(yy[-1][0], yy[-1][1])
    # plt.show()

