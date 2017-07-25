import context
import ops
import numpy as np
import os

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

def light(l):
    return "green" if l is 'G' else "red"

alphas = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]

for alpha in alphas:
    run_name = 'bias-{}'.format(alpha)
    plt_title = '$\\alpha$-{}'.format(alpha)
    fname = run_name + '-rmse.pkl'

    lights = ['G', 'R']

    rmse = ops.load_pkl(os.path.join('results', fname))

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

        blue = '#4295f4'
        red = '#f44245'
        green = '#42f471'
        yellow = '#f4f442'
        purp = '#9b42f4'
        dank_blue = '#5042f4'
        blood_orange = '#f46242'
        pink = '#f4427d'

        rects1 = ax.bar(ind, baseline_1_means, width, color=blue, yerr=baseline_1_std_errs)
        rects2 = ax.bar(ind + width, baseline_2_means, width, color=red, yerr=baseline_2_std_errs)
        rects3 = ax.bar(ind + 2 * width, kf_1_means, width, color=green, yerr=kf_1_std_errs)
        rects4 = ax.bar(ind + 3 * width, kf_2_means, width, color=yellow, yerr=kf_2_std_errs)
        rects5 = ax.bar(ind + 4 * width, ekf_1_means, width, color=purp, yerr=ekf_1_std_errs)
        rects6 = ax.bar(ind + 5 * width, ekf_2_means, width, color=dank_blue, yerr=ekf_2_std_errs)
        rects7 = ax.bar(ind + 6 * width, pf_1_means, width, color=blood_orange, yerr=pf_1_std_errs)
        rects8 = ax.bar(ind + 7 * width, pf_2_means, width, color=pink, yerr=pf_2_std_errs)

        hfont = {'fontname': 'Arial', 'size': 22}
        hfont2 = {'fontname': 'Arial', 'size': 16}

        # add some text for labels, title and axes ticks
        ax.set_ylabel('RMSE (meters)', hfont2)
        ax.set_title('{}-{}-light'.format(plt_title, light(l)), **hfont)
        ax.set_xticks(ind + width / 2)
        ax.set_xticklabels(('UTM Easting', 'UTM Northing'), **hfont2)
        plt.setp(ax.get_yticklabels(), fontsize=18)
        ax.grid(True)
        ax.legend((rects1[0], rects2[0], rects3[0], rects4[0], rects5[0], rects6[0], rects7[0], rects8[0]),
                  ('Baseline CV', 'Baseline CA', 'KF CV', 'KF CA', 'EKF CV', 'EKF CA', 'PF CV', 'PF CA'), loc='best', fontsize=14)
        fig.set_size_inches(8, 8)

        fig.savefig(os.path.join('results2', '{}-{}-light.png'.format(run_name, light(l))), dpi=100)
        #plt.show()
