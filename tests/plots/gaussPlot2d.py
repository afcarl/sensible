"""
Python implementation of gaussPlot2d.m from https://github.com/probml/pmtk3
"""
import matplotlib.pyplot as plt
import numpy as np


def gauss_plot_2d(mu, sigma, chi_square=9.488, data=None, label='', color='k', annotation=''):

    d, u = np.linalg.eig(sigma)
    n = 100
    t = np.linspace(0, 2 * np.pi, n)
    xy = np.array([np.cos(t), np.sin(t)])
    # k = sqrt(chi2inv(0.95, 4)) ~ 9.488
    k = np.sqrt(chi_square)
    w = np.matmul((k * u * np.sqrt(d)), xy)
    z = (mu * np.ones([2, n])) + w

    plt.plot(z[0, :], z[1, :], 'r')
    plt.scatter(mu[0][0], mu[1][0], c=color, label=label)
    plt.annotate(annotation, (mu[0][0], mu[1][0]))

    if data is not None:
        plt.scatter(data[0], data[1], c='g')
