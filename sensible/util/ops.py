import numpy as np
import scipy.linalg

from .exceptions import ParseError


def verify(val, min_val, max_val):
    """If val < min or val > max, raise a ParseError

    Throws a ParseError

    :param val:
    :param min_val:
    :param max_val:
    :return:
    """
    if val < min_val or val > max_val:
        raise ParseError
    else:
        return val


def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val -= (1 << bits)  # compute negative value
    return val  # return positive value as is


def mahalanobis(observation, mean, covariance):
    dx = observation - mean
    return dx.T * scipy.linalg.inv(covariance) * dx
