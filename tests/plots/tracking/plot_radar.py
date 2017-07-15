from __future__ import absolute_import

import cPickle as pickle
import os

import gaussPlot2d
import matplotlib

matplotlib.use('Qt4Agg')
import numpy as np

PICKLE_DIR='C:\\Users\\pemami\\Workspace\\Github\\sensible\\tests\\data\\trajectories\\'
RADAR_MSG='C:\\Users\\pemami\\Workspace\\Github\\sensible\\tests\\data\\trajectories\\radar-16-35-36200.pkl'


if __name__ == '__main__':

    kf = []

    files = ['kf-16-35-35600.pkl', 'kf-16-35-35800.pkl', 'kf-16-35-36000.pkl',
             'kf-16-35-36200.pkl', 'kf-16-35-36400.pkl', 'kf-16-35-36600.pkl',
             'kf-16-35-36800.pkl']

    with open(RADAR_MSG, 'r') as f:
        radar = pickle.load(f)

    # for f in files:
    #     with open(os.path.join(PICKLE_DIR, f), 'r') as myfile:
    #         kf.append(pickle.load(myfile))

    # Plot mahalanobis distance w.r.t. time
    # x = [-0.6, -.4, -.2, 0, .2, .4, .6]
    # # position plot
    # plt.figure(1)
    # plt.subplot(121)
    # dataMD = []
    # dataPosX = []
    # dataPosY = []
    # dataPosXdot = []
    # dataPosYdot = []
    # for idx, kk in enumerate(kf):
    #     md = ops.mahalanobis(radar['radar'], kk['kf'], kk['cov'])
    #
    #     dataPosX.append(kk['kf'][0])
    #     dataPosXdot.append(kk['kf'][1])
    #     dataPosY.append(kk['kf'][2])
    #     dataPosYdot.append(kk['kf'][3])
    #
    #     dataMD.append(md)
    #
    # plt.plot(x, dataMD)
    #
    # plt.subplot(122)
    # plt.scatter(dataPosX, dataPosY, c='b')
    # plt.scatter(radar['radar'][0], radar['radar'][2], c='r')
    # #plt.show()
    #
    # plt.figure(2)
    # plt.scatter(dataPosXdot, dataPosYdot, c='b')
    # plt.scatter(radar['radar'][1], radar['radar'][3], c='r')
    #
    # plt.show()

    # Plot 2d Gaussians, one for position and one for speed
    with open(os.path.join(PICKLE_DIR, files[4]), 'r') as myfile:
        kf.append(pickle.load(myfile))

    mu = kf[0]['m']
    sigma = kf[0]['cov']
    #mu[2] = 3278336.2

    #kalman = KalmanFilter(0.2)

    x_mu = np.array([[mu[0]], [mu[1]]])
    y_mu = np.array([[mu[2]], [mu[3]]])

    x_cov = sigma[0:2, 0:2]
    y_cov = sigma[2:4, 2:4]

    # md = kalman.mahalanobis(radar['radar'])
    # print("MD is: {}".format(md))

    print("Plotting 95% probability mass for x component of state")

    gaussPlot2d.gauss_plot_2d(x_mu, x_cov, data=radar['radar'][0:2])

    print("Plotting 95% probability mass for y component of state")

    gaussPlot2d.gauss_plot_2d(y_mu, y_cov, data=radar['radar'][2:4])