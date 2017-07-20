import ops
import os
import sensible
import numpy as np

from sensible.tracking.track import Track
from sensible.sensors.DSRC import DSRC

"""
Track 0, MM: CV, RMSE UTM Easting: 0.342325507492
Track 0, MM: CV, RMSE UTM Northing: 3.67996041606
Track 0, MM: CA, RMSE UTM Easting: 0.909723591125
Track 0, MM: CA, RMSE UTM Northing: 24.419041425
Track 1, MM: CV, RMSE UTM Easting: 0.510691044771
Track 1, MM: CV, RMSE UTM Northing: 4.35841503925
Track 1, MM: CA, RMSE UTM Easting: 1.2455773412
Track 1, MM: CA, RMSE UTM Northing: 3.88304570435
Track 2, MM: CV, RMSE UTM Easting: 0.212644096487
Track 2, MM: CV, RMSE UTM Northing: 3.48643810347
Track 2, MM: CA, RMSE UTM Easting: 0.964454187914
Track 2, MM: CA, RMSE UTM Northing: 3.99050035058
Track 3, MM: CV, RMSE UTM Easting: 0.394284936009
Track 3, MM: CV, RMSE UTM Northing: 4.28648025769
Track 3, MM: CA, RMSE UTM Easting: 0.648684076996
Track 3, MM: CA, RMSE UTM Northing: 4.5529852018
Track 4, MM: CV, RMSE UTM Easting: 0.135165217747
Track 4, MM: CV, RMSE UTM Northing: 4.13603967613
Track 4, MM: CA, RMSE UTM Easting: 1.14096963493
Track 4, MM: CA, RMSE UTM Northing: 4.57283286202
Track 5, MM: CV, RMSE UTM Easting: 0.257735378802
Track 5, MM: CV, RMSE UTM Northing: 4.62248683208
Track 5, MM: CA, RMSE UTM Easting: 0.929317169015
Track 5, MM: CA, RMSE UTM Northing: 8.28115671382
Track 6, MM: CV, RMSE UTM Easting: 0.344113873395
Track 6, MM: CV, RMSE UTM Northing: 4.37801968038
Track 6, MM: CA, RMSE UTM Easting: 1.02254029769
Track 6, MM: CA, RMSE UTM Northing: 4.77830756708
"""

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

            ekf_track = Track(dt=0.1, first_msg=fmesg, motion_model=m, sensor=DSRC, n_scan=1)

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

                ekf_track.state_estimator.y.append(msg)
                ekf_track.state_estimator.t.append(None)
                if len(ekf_track.state_estimator.y) >= 2 and len(ekf_track.state_estimator.x_k) == 0:
                    ekf_track.state_estimator.x_k.append(ekf_track.state_estimator.sensor_cfg.init_state(
                        ekf_track.state_estimator.y[-1],
                        ekf_track.state_estimator.y[-2],
                        0.1))
                    ekf_track.state_estimator.x_k_fused.append(None)
                    ekf_track.state_estimator.no_step = True

                ekf_track.step()

                if len(ekf_track.state_estimator.x_k) == 0:
                    continue
                else:
                    N += 1
                    # compute RMSE with gps_x, gps_y
                    gt_x = gps_x[ii][idx]
                    gt_y = gps_y[ii][idx]

                    x_k = ekf_track.state_estimator.x_k[-1]

                    rmse_utm_x.append((gt_x - x_k[0]) ** 2)
                    if m == 'CV':
                        rmse_utm_y.append((gt_y - x_k[2]) ** 2)
                    else:
                        rmse_utm_y.append((gt_y - x_k[3]) ** 2)

            rmse_utm_x = np.sqrt(np.sum(np.array([rmse_utm_x]))/N)
            rmse_utm_y = np.sqrt(np.sum(np.array([rmse_utm_y]))/N)

            print('Track {}, MM: {}, RMSE UTM Easting: {}'.format(ii, m, rmse_utm_x))
            print('Track {}, MM: {}, RMSE UTM Northing: {}'.format(ii, m, rmse_utm_y))