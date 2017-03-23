import numpy as np
import scipy.linalg


def verify(val, min_val, max_val):
    """If val < min or val > max, raise a ParseError

    :param val:
    :param min_val:
    :param max_val:
    :return:
    """
    if val < min_val or val > max_val:
        raise ValueError("Value {} out of min bound: {} "
                         "and max bound: {}".format(val, min_val, max_val))
    else:
        return val


def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val -= (1 << bits)  # compute negative value
    return val  # return positive value as is


def mahalanobis(observation, mean, covariance):
    dx = observation - mean
    return np.matmul(dx.T, np.matmul(scipy.linalg.inv(covariance), dx))
