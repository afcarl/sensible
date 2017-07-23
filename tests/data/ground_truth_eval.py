import ops
import os
import context
import sensible
import numpy as np
import sys

import matplotlib.pyplot as plt

from sensible.tracking.track import Track
from sensible.sensors.DSRC import DSRC


if __name__ == '__main__':
    N_TRACKS = 8
    # Test each run 1 by 1
    # data_dir = 'SW-16-SW-13'
    data_dir = 'test_data'
    data_dir2 = 'SW-16-SW-13'
    
    suitcase_x = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_x.pkl'))
    suitcase_y = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_y.pkl'))
    suitcase_heading = ops.load_pkl(os.path.join(data_dir, 'suitcase_heading.pkl'))
    suitcase_speed = ops.load_pkl(os.path.join(data_dir, 'suitcase_speed.pkl'))
    
    gps_x = ops.load_pkl(os.path.join(data_dir, 'gps_x.pkl'))
    gps_y = ops.load_pkl(os.path.join(data_dir, 'gps_y.pkl'))
    
    suitcase_x.append(ops.load_pkl(os.path.join(data_dir2, 'suitcase_gps_x.pkl'))[0])
    suitcase_y.append(ops.load_pkl(os.path.join(data_dir2, 'suitcase_gps_y.pkl'))[0])
    suitcase_heading.append(ops.load_pkl(os.path.join(data_dir2, 'suitcase_heading.pkl'))[0])
    suitcase_speed.append(ops.load_pkl(os.path.join(data_dir2, 'suitcase_speed.pkl'))[0])

    gps_x.append(ops.load_pkl(os.path.join(data_dir2, 'gps_x.pkl'))[0])
    gps_y.append(ops.load_pkl(os.path.join(data_dir2, 'gps_y.pkl'))[0])
    
    track_2_start = 27
    track_7_start = 10

    mms = ['CV', 'CA']
    #filters = ['PF']
    filters = ['Baseline', 'KF', 'EKF', 'PF']
    fmesg = {
        'id': 0,
        'max_accel': -1,
        'max_decel': -1,
        'lane': 4,
        'veh_len': 4.
    }
        
    # 0 is Baseline
    # 1 is KF
    # 2 is EKF
    # 3 is PF

    # FOr each filter,
    # Take UTM East and UTM N average over all green light tracks,
    # where each track result is the RMSE for CV and CA. Repeat
    # for red lights.
  
    green = (1, 3, 4, 5)
    red = (0, 2, 6, 7)
    
    rmse = {}

    for ii in range(N_TRACKS):
        rmse[ii] = {}

        for filt_id, filt in enumerate(filters):
            
            rmse[ii][filt] = {}

            for m in mms:
                
                rmse[ii][filt][m] = {}
                rmse[ii][filt][m]['utm_e'] = []
                rmse[ii][filt][m]['utm_n'] = []

                if filt is not 'Baseline':
                    #print('{}-{}\n'.format(filt, m))
                    track = Track(dt=0.1, first_msg=fmesg, motion_model=m, sensor=DSRC,
                            n_scan=1, filter=filt, use_bias_estimation=True)

                if ii == 2:
                    start = track_2_start
                elif ii == 0:
                    # TODO: change back to 1 when SW-42
                    #start = 6
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
                    
                    if filt is 'Baseline':
                        gt_x = gps_x[ii][idx]
                        gt_y = gps_y[ii][idx]
                        rmse[ii][filt][m]['utm_e'].append((gt_x - utm_e) ** 2)
                        rmse[ii][filt][m]['utm_n'].append((gt_y - utm_n) ** 2)
                        continue
                    if filt is 'PF':
                        continue

                    theta = (-theta + 90.)

                    msg = np.array([utm_e, utm_n, v, theta])

                    track.state_estimator.y.append(msg)
                    track.state_estimator.t.append(None)
                    if len(track.state_estimator.y) >= 2 and len(track.state_estimator.x_k) == 0:
                        track.state_estimator.x_k.append(track.state_estimator.init_state())
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
                        
                        if m is 'CV':
                            rmse[ii][filt][m]['utm_e'].append((gt_x - x_k[0]) ** 2)
                            rmse[ii][filt][m]['utm_n'].append((gt_y - x_k[2]) ** 2)
                        elif m is 'CA':
                            rmse[ii][filt][m]['utm_e'].append((gt_x - x_k[0]) ** 2)
                            rmse[ii][filt][m]['utm_n'].append((gt_y - x_k[3]) ** 2)
                        
                        # TODO: write results as CSV to log file for later plotting sample trajectories
                    
                # compute RMSE 
                rmse[ii][filt][m]['utm_e'] = np.sqrt(np.mean(rmse[ii][filt][m]['utm_e']))
                rmse[ii][filt][m]['utm_n'] = np.sqrt(np.mean(rmse[ii][filt][m]['utm_n']))

    lights = ['G', 'R']

    # compute the average over all tracks for CV and CA, UTM Easting and UTM Northing, per filter 
    for filt in filters:
        rmse[filt] = {}
        for m in mms:
            rmse[filt][m] = {}
         
            rmse[filt][m]['avg_utm_e'] = {}
            rmse[filt][m]['avg_utm_n'] = {}
            rmse[filt][m]['std_utm_e'] = {}
            rmse[filt][m]['std_utm_n'] = {}
            
            for l in lights:
                rmse[filt][m]['avg_utm_e'][l] = []
                rmse[filt][m]['avg_utm_n'][l] = []
                rmse[filt][m]['std_utm_e'][l] = []
                rmse[filt][m]['std_utm_n'][l] = []
                
                # collect the data over tracks
                for ii in range(N_TRACKS):
                    if l == 'G':
                        if ii in green:
                            rmse[filt][m]['avg_utm_e'][l].append(rmse[ii][filt][m]['utm_e'])
                            rmse[filt][m]['std_utm_e'][l].append(rmse[ii][filt][m]['utm_e'])
                            rmse[filt][m]['avg_utm_n'][l].append(rmse[ii][filt][m]['utm_n'])
                            rmse[filt][m]['std_utm_n'][l].append(rmse[ii][filt][m]['utm_n'])
                    elif l == 'R':
                        if ii in red:
                            rmse[filt][m]['avg_utm_e'][l].append(rmse[ii][filt][m]['utm_e'])
                            rmse[filt][m]['std_utm_e'][l].append(rmse[ii][filt][m]['utm_e'])
                            rmse[filt][m]['avg_utm_n'][l].append(rmse[ii][filt][m]['utm_n'])
                            rmse[filt][m]['std_utm_n'][l].append(rmse[ii][filt][m]['utm_n'])
                            
                rmse[filt][m]['avg_utm_e'][l] = np.mean(rmse[filt][m]['avg_utm_e'][l])
                rmse[filt][m]['std_utm_e'][l] = np.std(rmse[filt][m]['std_utm_e'][l])
                rmse[filt][m]['avg_utm_n'][l] = np.mean(rmse[filt][m]['avg_utm_n'][l])
                rmse[filt][m]['std_utm_n'][l] = np.std(rmse[filt][m]['std_utm_n'][l])
            
    for l in lights:
        N = 2
        ind = np.arange(N)
        width = 0.1
        fig, ax = plt.subplots()
        # rect1 = baseline CV (bar1= UTM Easting, bar2= UTM Northing)
        # rect2 = baseline CA (bar1 = UTM Easting, bar2 = UTM NOrthing)
        # rect3 = KF
        # rect5 = EKF
        # rect7 = PF
        baseline_1_means = (rmse['Baseline']['CV']['avg_utm_e'][l], rmse['Baseline']['CV']['avg_utm_n'][l])
        baseline_1_std_errs = (rmse['Baseline']['CV']['std_utm_e'][l], rmse['Baseline']['CV']['std_utm_n'][l])
        baseline_2_means = (rmse['Baseline']['CA']['avg_utm_e'][l], rmse['Baseline']['CA']['avg_utm_n'][l])
        baseline_2_std_errs = (rmse['Baseline']['CA']['std_utm_e'][l], rmse['Baseline']['CA']['std_utm_n'][l])
        kf_1_means = (rmse['KF']['CV']['avg_utm_e'][l], rmse['KF']['CV']['avg_utm_n'][l])
        kf_1_std_errs = (rmse['KF']['CV']['std_utm_e'][l], rmse['KF']['CV']['std_utm_n'][l])
        kf_2_means = (rmse['KF']['CA']['avg_utm_e'][l], rmse['KF']['CA']['avg_utm_n'][l])
        kf_2_std_errs = (rmse['KF']['CA']['std_utm_e'][l], rmse['KF']['CA']['std_utm_n'][l])
        ekf_1_means = (rmse['EKF']['CV']['avg_utm_e'][l], rmse['EKF']['CV']['avg_utm_n'][l])
        ekf_1_std_errs = (rmse['EKF']['CV']['std_utm_e'][l], rmse['EKF']['CV']['std_utm_n'][l])
        ekf_2_means = (rmse['EKF']['CA']['avg_utm_e'][l], rmse['EKF']['CA']['avg_utm_n'][l])
        ekf_2_std_errs = (rmse['EKF']['CA']['std_utm_e'][l], rmse['EKF']['CA']['std_utm_n'][l])
        pf_1_means = (rmse['PF']['CV']['avg_utm_e'][l], rmse['PF']['CV']['avg_utm_n'][l])
        pf_1_std_errs = (rmse['PF']['CV']['std_utm_e'][l], rmse['PF']['CV']['std_utm_n'][l])
        pf_2_means = (rmse['PF']['CA']['avg_utm_e'][l], rmse['PF']['CA']['avg_utm_n'][l])
        pf_2_std_errs = (rmse['PF']['CA']['std_utm_e'][l], rmse['PF']['CA']['std_utm_n'][l])
        
        rects1 = ax.bar(ind, baseline_1_means, width, color='g', yerr=baseline_1_std_errs)
        rects2 = ax.bar(ind + width, baseline_2_means, width, color='b', yerr=baseline_2_std_errs)
        rects3 = ax.bar(ind + 2*width, kf_1_means, width, color='m', yerr=kf_1_std_errs)
        rects4 = ax.bar(ind + 3*width, kf_2_means, width, color='c', yerr=kf_2_std_errs)
        rects5 = ax.bar(ind + 4*width, ekf_1_means, width, color='r', yerr=ekf_1_std_errs)
        rects6 = ax.bar(ind + 5*width, ekf_2_means, width, color='b', yerr=ekf_2_std_errs)
        rects7 = ax.bar(ind + 6*width, pf_1_means, width, color='g', yerr=pf_1_std_errs)
        rects8 = ax.bar(ind + 7*width, pf_2_means, width, color='y', yerr=pf_2_std_errs)

        # add some text for labels, title and axes ticks
        ax.set_ylabel('RMSE (meters)')
        ax.set_title('Bias + Covariance Rotation for {} light'.format(l))
        ax.set_xticks(ind + width / 2)
        ax.set_xticklabels(('UTM Easting', 'UTM Northing'))
        ax.grid(True)
        ax.legend((rects1[0], rects2[0], rects3[0], rects4[0], rects5[0], rects6[0],rects7[0], rects8[0]), 
                ('Baseline CV', 'Baseline CA', 'KF CV', 'KF CA', 'EKF CV', 'EKF CA', 'PF CV', 'PF CA'))

        plt.show()
