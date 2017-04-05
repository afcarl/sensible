from __future__ import division

from sensible.tracking.state_estimator import StateEstimator

import numpy as np
import scipy.linalg


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """
    def __init__(self, sensor_kf):
        super(KalmanFilter, self).__init__()
        self.Q = sensor_kf.Q
        self.P = sensor_kf.P
        self.F = sensor_kf.F
        self.R = sensor_kf.R

        self.sensor_kf = sensor_kf

    def parse_msg(self, msg):
        return self.sensor_kf.parse_msg(msg)

    def measurement_residual_covariance(self):
        return self.P + self.R

    def process_covariance(self):
        return self.P

    def step(self):

        m, _ = self.get_latest_message()

        if not self.k < len(self.x_k):
            print(" warning: error")

        x_k_bar = np.matmul(self.F, self.x_k[self.k]) + np.matmul(self.Q, np.random.normal(size=4))
        # state covariance prediction
        self.P = np.matmul(self.F, np.matmul(self.P, self.F.T)) + self.Q
        # measurement prediction
        self.y_k.append(x_k_bar + np.matmul(self.R, np.random.normal(size=4)))
        # innovation
        # if no new measurements, e_k is 0.
        e_k = (m - self.y_k[self.k]) if m is not None else np.zeros([4])

        # K_k = P * inv(P + R)
        u = scipy.linalg.inv(self.P + self.R)
        K_k = np.matmul(self.P, u)
        # l = scipy.linalg.cho_factor(self.P + self.R)
        # u = scipy.linalg.cho_solve(l, np.eye(4))
        # K_k = np.matmul(self.P, scipy.linalg.solve(l[0].T, u, sym_pos=True, lower=True))
        # state update
        self.x_k.append(x_k_bar + np.matmul(K_k, e_k))
        # covariance update
        self.P -= np.matmul(K_k, self.P)

        #print("  [*] Kalman step {}".format(self.k))
