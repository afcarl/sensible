import numpy as np
import scipy.linalg
from sensible.util import ops
from sensible.util import time_stamp as ts
import os


class StateEstimator(object):
    """
    Super class for state estimation. Presents a common
    interface that can be used by the TrackSpecialist for any
    specific implementation.

    """
    def __init__(self, use_cov_intersection):
        self.y = []  # messages
        self.x_k = []  # filtered track state
        self.y_k = []  # filtered measurement
        self.x_k_fused = []  # result of the covariance intersection algorithm
        self.t = []  # time stamps
        self.k = -1  # current time step
        self._use_cov_intersection = use_cov_intersection

    def get_latest_message(self):
        """
        Returns the latest message
        :return:
        """
        if -1 < self.k < len(self.y):
            t = self.t[self.k]
            t_string = t.to_string() if t is not None else ts.unavailable()
            return self.y[self.k], t_string
        else:
            return None, None

    def state(self):
        """Return the latest Kalman Filter prediction of the state, and the timestamp."""
        if -1 < self.k <= len(self.x_k):
            t = self.t[self.k]
            t_string = t.to_fname_string() if t is not None else ts.unavailable()
            if not self._use_cov_intersection:
                return self.x_k[self.k+1], t_string
            else:
                return self.x_k_fused[self.k+1], t_string
        else:
            return None, None

    def measurement(self):
        """Return the latest Kalman Filter prediction of the measurement, and the timestamp."""
        if -1 < self.k < len(self.y_k):
            t = self.t[self.k]
            t_string = t.to_fname_string() if t is not None else ts.unavailable()
            return self.y_k[self.k], t_string
        else:
            return None, None

    def store(self, msg, time):
        self.k += 1
        if msg is None:
            self.y.append(None)
            self.t.append(None)
        else:
            self.y.append(self.parse_msg(msg))
            self.t.append(time)
            if self.k == 0:
                self.x_k.append(self.y[self.k])
                self.x_k_fused.append(None)

    def save_measurement(self, destination):
        yk, t_stamp = self.measurement()
        cov = self.measurement_residual_covariance()
        ops.dump({'time': t_stamp, 'm': yk, 'cov': cov},
                 os.path.join(destination, 'kf-measurement-', t_stamp, '.pkl'))

    def save_state(self, destination):
        xk, t_stamp = self.state()
        cov = self.process_covariance()
        ops.dump({'time': t_stamp, 'm': xk, 'cov': cov},
                 os.path.join(destination, 'kf-state-', t_stamp, '.pkl'))

    def mahalanobis(self, s, P):
        """
        Compute the track-to-track or measurement-to-track mahalanobis distance
        between track state or measurement `s` and the estimated state of this track

        :param s: measurement [x, xdot, y, ydot]
        :param P: covariance of s
        :return: the M distance
        """
        # TODO: Add cross-cov terms
        ss = self.state()
        PP = self.process_covariance()

        if np.shape(PP)[0] == 4:
            PP = PP[2:4, 2:4]

        dx = s - ss
        return np.matmul(dx.T, np.matmul(scipy.linalg.inv(PP + P), dx))

    def measurement_residual_covariance(self):
        raise NotImplementedError

    def step(self):
        """One iteration of a discrete-time filtering algorithm.
        Uses the latest message saved by calling self.store(msg).
        """
        raise NotImplementedError

    def process_covariance(self):
        raise NotImplementedError

    def parse_msg(self, msg):
        raise NotImplementedError

    def covariance_intersection(self, b_bar, P_b_bar):
        """
        The mean estimate, b_bar, and covariance estimate, P_b_bar, from the
        state estimator for sensor B.
        To be fused with this state estimator's current mean and cov estimates.
        :param b_bar:
        :param Pb_bar:
        :return:
        """
        raise NotImplementedError