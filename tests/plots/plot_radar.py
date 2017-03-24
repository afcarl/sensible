import cPickle as pickle
import os
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from sensible.util import ops
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

    for f in files:
        with open(os.path.join(PICKLE_DIR, f), 'r') as myfile:
            kf.append(pickle.load(myfile))

    x = [-0.6, -.4, -.2, 0, .2, .4, .6]
    # position plot
    plt.figure(1)
    plt.subplot(121)
    dataMD = []
    dataPosX = []
    dataPosY = []
    dataPosXdot = []
    dataPosYdot = []
    for idx, kk in enumerate(kf):
        md = ops.mahalanobis(radar['radar'], kk['kf'], kk['cov'])

        dataPosX.append(kk['kf'][0])
        dataPosXdot.append(kk['kf'][1])
        dataPosY.append(kk['kf'][2])
        dataPosYdot.append(kk['kf'][3])

        dataMD.append(md)

    plt.plot(x, dataMD)

    plt.subplot(122)
    plt.scatter(dataPosX, dataPosY, c='b')
    plt.scatter(radar['radar'][0], radar['radar'][2], c='r')
    #plt.show()

    plt.figure(2)
    plt.scatter(dataPosXdot, dataPosYdot, c='b')
    plt.scatter(radar['radar'][1], radar['radar'][3], c='r')

    plt.show()