import ops
import os
import context
import sensible
import numpy as np

from sensible.tracking.track import Track
from sensible.sensors.DSRC import DSRC


if __name__ == '__main__':
    # Test each run 1 by 1
    # data_dir = 'SW-16-SW-13'
    data_dir = 'test_data'
    suitcase_x = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_x.pkl'))
    suitcase_y = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_y.pkl'))
    suitcase_heading = ops.load_pkl(os.path.join(data_dir, 'suitcase_heading.pkl'))
    suitcase_speed = ops.load_pkl(os.path.join(data_dir, 'suitcase_speed.pkl'))

    gps_x = ops.load_pkl(os.path.join(data_dir, 'gps_x.pkl'))
    gps_y = ops.load_pkl(os.path.join(data_dir, 'gps_y.pkl'))

    track_2_start = 27
    track_7_start = 10

    mms = ['CV', 'CA']
    filters = ['KF', 'EKF', 'PF']
    fmesg = {
        'id': 0,
        'max_accel': -1,
        'max_decel': -1,
        'lane': 4,
        'veh_len': 4.
    }

    for ii in range(7):

        for m in mms:
            rmse_utm_x = []
            rmse_utm_y = []

            track = Track(dt=0.1, first_msg=fmesg, motion_model=m, sensor=DSRC, n_scan=1, filter='PF')

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
                    # track.state_estimator.x_k.append(track.state_estimator.sensor_cfg.init_state(
                    #     track.state_estimator.y[-1],
                    #     track.state_estimator.y[-2],
                    #     0.1))
                    track.state_estimator.x_k.append(track.state_estimator.init_state())
                    track.state_estimator.x_k_fused.append(None)
                    track.state_estimator.no_step = True

                track.step()

                if len(track.state_estimator.x_k) == 0:
                    continue
                else:
                    N += 1
                    # compute RMSE with gps_x, gps_y
                    gt_x = gps_x[ii][idx]
                    gt_y = gps_y[ii][idx]

                    x_k = track.state_estimator.x_k[-1]

                    rmse_utm_x.append((gt_x - x_k[0]) ** 2)
                    if m == 'CV':
                        rmse_utm_y.append((gt_y - x_k[2]) ** 2)
                    else:
                        rmse_utm_y.append((gt_y - x_k[3]) ** 2)

            rmse_utm_x = np.sqrt(np.sum(np.array([rmse_utm_x]))/N)
            rmse_utm_y = np.sqrt(np.sum(np.array([rmse_utm_y]))/N)

            print('Track {}, MM: {}, RMSE UTM Easting: {}'.format(ii, m, rmse_utm_x))
            print('Track {}, MM: {}, RMSE UTM Northing: {}'.format(ii, m, rmse_utm_y))