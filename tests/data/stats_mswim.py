import context
import ops
import numpy as np
import os

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR = 'results3'

def light(l):
    return "green" if l is 'G' else "red"

alphas = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]


x = 0.0

for alpha in alphas:
    if alpha == x:
        print('Alpha: {}'.format(alpha))

        run_name = 'bias-{}'.format(alpha)
        plt_title = '$\\alpha$-{}'.format(alpha)
        fname = run_name + '-rmse.pkl'
        track_fname = run_name + '-tracks.pkl'

        lights = ['G', 'R']

        rmse = ops.load_pkl(os.path.join(DATA_DIR, fname))
        tracks = ops.load_pkl(os.path.join(DATA_DIR, track_fname))
        
        fig, ax = plt.subplots()
        ax.grid(True)
        hfont = {'fontname':'Arial', 'size': 16}
        ax.set_xlabel('UTM Easting (meters)', **hfont)
        ax.set_ylabel('UTM Northing (meters)', **hfont)
        ax.set_title('$\\alpha$-{}-green-light'.format(x))
        # green light
        ax.plot(tracks[3]['KF']['CV']['utm_e'], tracks[3]['KF']['CV']['utm_n'], '--', label='LKF', lw=3)
        ax.plot(tracks[3]['EKF']['CV']['utm_e'], tracks[3]['EKF']['CV']['utm_n'], '-', label='EKF', lw=3)
        ax.plot(tracks[3]['PF']['CV']['utm_e'], tracks[3]['PF']['CV']['utm_n'], ':', label='PF', lw=3)
        ax.plot(tracks[3]['Baseline']['CV']['utm_e'], tracks[3]['Baseline']['CV']['utm_n'], label='Baseline', lw=2)

        ax.legend()
        fig.set_size_inches(8,8)
        fig.savefig(os.path.join(DATA_DIR, 'traj-green.png'), dpi=100)

        plt.close()

        # red light
        fig, ax = plt.subplots()
        ax.grid(True)
        hfont = {'fontname':'Arial', 'size': 16}
        ax.set_xlabel('UTM Easting (meters)', **hfont)
        ax.set_ylabel('UTM Northing (meters)', **hfont)
        ax.set_title('$\\alpha$-{}-red-light'.format(x))
        ax.plot(tracks[6]['KF']['CV']['utm_e'], tracks[6]['KF']['CV']['utm_n'], '--', label='LKF', lw=3)
        ax.plot(tracks[6]['EKF']['CV']['utm_e'], tracks[6]['EKF']['CV']['utm_n'], '-', label='EKF', lw=3)
        ax.plot(tracks[6]['PF']['CV']['utm_e'], tracks[6]['PF']['CV']['utm_n'], ':', label='PF', lw=3)
        ax.plot(tracks[6]['Baseline']['CV']['utm_e'], tracks[6]['Baseline']['CV']['utm_n'], label='Baseline', lw=2)
        ax.legend()
        fig.set_size_inches(8,8)
        fig.savefig(os.path.join(DATA_DIR, 'traj-red.png'), dpi=100)

        plt.close()
        """
        for l in lights:
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
            
            print('Light: {}'.format(light(l)))
            print('baseline')
            print(baseline_1_means, baseline_1_std_errs)
            print(baseline_2_means, baseline_2_std_errs)
            print('kf')
            print(kf_1_means, kf_1_std_errs)
            print(kf_2_means, kf_2_std_errs)
            print('ekf')
            print(ekf_1_means, ekf_1_std_errs)
            print(ekf_2_means, ekf_2_std_errs)
            print('pf')
            print(pf_1_means, pf_1_std_errs)
            print(pf_2_means, pf_2_std_errs)
            print('\n')
        """
