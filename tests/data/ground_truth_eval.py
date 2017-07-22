import ops
import os
import context
import sensible
import numpy as np

import matplotlib.pyplot as plt

from sensible.tracking.track import Track
from sensible.sensors.DSRC import DSRC


if __name__ == '__main__':
    # Test each run 1 by 1
    # data_dir = 'SW-16-SW-13'
    data_dir = 'test_data'
    data_dir2 = 'SW-16-SW-13'

    # suitcase_x = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_x.pkl'))
    # suitcase_y = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_y.pkl'))
    # suitcase_heading = ops.load_pkl(os.path.join(data_dir, 'suitcase_heading.pkl'))
    # suitcase_speed = ops.load_pkl(os.path.join(data_dir, 'suitcase_speed.pkl'))
    #
    # gps_x = ops.load_pkl(os.path.join(data_dir, 'gps_x.pkl'))
    # gps_y = ops.load_pkl(os.path.join(data_dir, 'gps_y.pkl'))

    suitcase_x = ops.load_pkl(os.path.join(data_dir2, 'suitcase_gps_x.pkl'))
    suitcase_y = ops.load_pkl(os.path.join(data_dir2, 'suitcase_gps_y.pkl'))
    suitcase_heading = ops.load_pkl(os.path.join(data_dir2, 'suitcase_heading.pkl'))
    suitcase_speed = ops.load_pkl(os.path.join(data_dir2, 'suitcase_speed.pkl'))

    gps_x = ops.load_pkl(os.path.join(data_dir2, 'gps_x.pkl'))
    gps_y = ops.load_pkl(os.path.join(data_dir2, 'gps_y.pkl'))

    track_2_start = 27
    track_7_start = 10

    mms = ['CV', 'CA']
    filters = ['KF', 'EKF']
    fmesg = {
        'id': 0,
        'max_accel': -1,
        'max_decel': -1,
        'lane': 4,
        'veh_len': 4.
    }

    kf_rmse_utm_x = [[], []]
    kf_rmse_utm_y = [[], []]
    ekf_rmse_utm_x = [[], []]
    ekf_rmse_utm_y = [[], []]

    avg_kf_rmse_utm_x = []
    avg_kf_rmse_utm_y = []
    avg_ekf_rmse_utm_x = []
    avg_ekf_rmse_utm_y = []

    std_kf_rmse_utm_x = []
    std_kf_rmse_utm_y = []
    std_ekf_rmse_utm_x = []
    std_ekf_rmse_utm_y = []

    kf_utm_x_cv = []
    kf_utm_x_ca = []
    kf_utm_y_cv = []
    kf_utm_y_ca = []
    ekf_utm_x_cv = []
    ekf_utm_x_ca = []
    ekf_utm_y_cv = []
    ekf_utm_y_ca = []

    for ii in range(1):
        for filt in filters:
            for m in mms:

                track = Track(dt=0.1, first_msg=fmesg, motion_model=m, sensor=DSRC, n_scan=1, filter=filt)

                if ii == 2:
                    start = track_2_start
                elif ii == 0:
                    start = 1
                elif ii == 6:
                    start = track_7_start
                else:
                    start = 0

                N = 0
                # Suitcase vs HP GPS northing error
                for idx, (utm_e, utm_n, theta, v) in enumerate(zip(suitcase_x[ii],
                                                                 suitcase_y[ii], suitcase_heading[ii], suitcase_speed[ii])):
                    if idx < start:
                        continue

                    if theta >= 0 or theta < 270.0:
                        theta += 90.
                    else:
                        theta -= 270.

                    msg = np.array([utm_e, utm_n, v, theta])

                    track.state_estimator.y.append(msg)
                    track.state_estimator.t.append(None)
                    if len(track.state_estimator.y) >= 2 and len(track.state_estimator.x_k) == 0:
                        track.state_estimator.x_k.append(track.state_estimator.sensor_cfg.init_state(
                            track.state_estimator.y[-1],
                            track.state_estimator.y[-2],
                            0.1))
                        #track.state_estimator.x_k.append(track.state_estimator.init_state())
                        track.state_estimator.x_k_fused.append(None)
                        track.state_estimator.no_step = True

                    track.step()

                    if len(track.state_estimator.x_k) == 0:
                        continue
                    else:
                        #N += 1
                        # compute RMSE with gps_x, gps_y
                        gt_x = gps_x[ii][idx]
                        gt_y = gps_y[ii][idx]

                        x_k = track.state_estimator.x_k[-1]

                        if filt is 'KF' and m is 'CV':
                            kf_rmse_utm_x[0].append((gt_x - x_k[0]) ** 2)
                            kf_rmse_utm_y[0].append((gt_y - x_k[2]) ** 2)
                        elif filt is 'KF' and m is 'CA':
                            kf_rmse_utm_x[1].append((gt_x - x_k[0]) ** 2)
                            kf_rmse_utm_y[1].append((gt_y - x_k[3]) ** 2)
                        elif filt is 'EKF' and m is 'CV':
                            ekf_rmse_utm_x[0].append((gt_x - x_k[0]) ** 2)
                            ekf_rmse_utm_y[0].append((gt_y - x_k[2]) ** 2)
                        elif filt is 'EKF' and m is 'CA':
                            ekf_rmse_utm_x[1].append((gt_x - x_k[0]) ** 2)
                            ekf_rmse_utm_y[1].append((gt_y - x_k[3]) ** 2)

        kf_utm_x_cv.append(np.sqrt(np.sum(np.array([kf_rmse_utm_x[0]])) / len(kf_rmse_utm_x[0])))
        kf_utm_x_ca.append(np.sqrt(np.sum(np.array([kf_rmse_utm_x[1]])) / len(kf_rmse_utm_x[1])))
        kf_utm_y_cv.append(np.sqrt(np.sum(np.array([kf_rmse_utm_y[0]])) / len(kf_rmse_utm_y[0])))
        kf_utm_y_ca.append(np.sqrt(np.sum(np.array([kf_rmse_utm_y[1]])) / len(kf_rmse_utm_y[1])))
        ekf_utm_x_cv.append(np.sqrt(np.sum(np.array([ekf_rmse_utm_x[0]])) / len(ekf_rmse_utm_x[0])))
        ekf_utm_x_ca.append(np.sqrt(np.sum(np.array([ekf_rmse_utm_x[1]])) / len(ekf_rmse_utm_x[1])))
        ekf_utm_y_cv.append(np.sqrt(np.sum(np.array([ekf_rmse_utm_y[0]])) / len(ekf_rmse_utm_y[0])))
        ekf_utm_y_ca.append(np.sqrt(np.sum(np.array([ekf_rmse_utm_y[1]])) / len(ekf_rmse_utm_y[1])))

        kf_rmse_utm_x = [[], []]
        kf_rmse_utm_y = [[], []]
        ekf_rmse_utm_x = [[], []]
        ekf_rmse_utm_y = [[], []]

    avg_kf_rmse_utm_x.append(np.mean(kf_utm_x_cv))
    avg_kf_rmse_utm_x.append(np.mean(kf_utm_x_ca))
    avg_kf_rmse_utm_y.append(np.mean(kf_utm_y_cv))
    avg_kf_rmse_utm_y.append(np.mean(kf_utm_y_ca))
    avg_ekf_rmse_utm_x.append(np.mean(ekf_utm_x_cv))
    avg_ekf_rmse_utm_x.append(np.mean(ekf_utm_x_ca))
    avg_ekf_rmse_utm_y.append(np.mean(ekf_utm_y_cv))
    avg_ekf_rmse_utm_y.append(np.mean(ekf_utm_y_ca))

    std_kf_rmse_utm_x.append(np.std(kf_utm_x_cv))
    std_kf_rmse_utm_x.append(np.std(kf_utm_x_ca))
    std_kf_rmse_utm_y.append(np.std(kf_utm_y_cv))
    std_kf_rmse_utm_y.append(np.std(kf_utm_y_ca))
    std_ekf_rmse_utm_x.append(np.std(ekf_utm_x_cv))
    std_ekf_rmse_utm_x.append(np.std(ekf_utm_x_ca))
    std_ekf_rmse_utm_y.append(np.std(ekf_utm_y_cv))
    std_ekf_rmse_utm_y.append(np.std(ekf_utm_y_ca))
     #print('Track {}, MM: {}, RMSE UTM Easting: {}'.format(ii, m, rmse_utm_x))
     #print('Track {}, MM: {}, RMSE UTM Northing: {}'.format(ii, m, rmse_utm_y))

    N = 2
    ind = np.arange(N)
    width = 0.1
    fig, ax = plt.subplots()
    # utm easting cv
    rects1 = ax.bar(ind, avg_kf_rmse_utm_x, width, color='g', yerr=std_kf_rmse_utm_x)
    rects2 = ax.bar(ind + width, avg_kf_rmse_utm_y, width, color='b', yerr=std_kf_rmse_utm_y)
    rects3 = ax.bar(ind + 2*width, avg_ekf_rmse_utm_x, width, color='m', yerr=std_ekf_rmse_utm_x)
    rects4 = ax.bar(ind + 3*width, avg_ekf_rmse_utm_y, width, color='c', yerr=std_ekf_rmse_utm_y)
    # rects5 = ax.bar(ind, avg_kf_rmse_utm_x[1], width, color='r', yerr=std_kf_rmse_utm_x[0])
    # rects6 = ax.bar(ind, avg_kf_rmse_utm_y[1], width, color='b', yerr=std_kf_rmse_utm_y[1])
    # rects7 = ax.bar(ind, avg_ekf_rmse_utm_x[1], width, color='g', yerr=std_ekf_rmse_utm_x[1])
    # rects8 = ax.bar(ind, avg_ekf_rmse_utm_y[1], width, color='y', yerr=std_ekf_rmse_utm_y[1])

    # add some text for labels, title and axes ticks
    ax.set_ylabel('RMSE (meters)')
    ax.set_title('KF vs EKF')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(('CV', 'CA'))
    ax.grid(True)
    ax.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('KF UTM Easting', 'KF UTM Northing', 'EKF UTM Easting', 'EKF UTM Northing'))

    plt.show()