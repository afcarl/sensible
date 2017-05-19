from sensible.tracking.state_estimator import StateEstimator

import numpy as np
import scipy.linalg

from collections import deque


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """

    def __init__(self, sensor_kf, sliding_window, fused_track=False):
        super(KalmanFilter, self).__init__(fused_track, sliding_window, sensor_kf.stationary_R)
        self.Q = sensor_kf.Q
        self.F = sensor_kf.F
        self.R = sensor_kf.R
        self.sensor_kf = sensor_kf
        self.P = deque(maxlen=sliding_window)
        self.P.append(sensor_kf.P)
        self.K = deque(maxlen=sliding_window)

    def parse_msg(self, msg, stationary_R=True):
        return self.sensor_kf.parse_msg(msg, stationary_R)

    def measurement_residual_covariance(self):
        return self.P[-1] + self.R

    def update_measurement_covariance(self, x_rms, y_rms):
        self.R = self.sensor_kf.update_measurement_covariance(x_rms, y_rms)

    def n_scan_mahalanobis(self, s2, p2_, K2_):
        s1, time = self.state(self.sliding_window)
        p1 = np.zeros((2, 2))
        p2 = np.zeros((2, 2))

        cross_cov_prev = np.zeros((2, 2))
        K1 = np.zeros((2, 2))
        F = np.array(self.F)
        Q = np.array(self.Q)

        dist_cc = 0.
        for i in range(self.sliding_window):
            if np.shape(self.P[i])[0] == 4:
                p1 = self.P[i][2:4, 2:4]
                K1 = np.array(self.K[i][2:4, 2:4])
                K2 = K2_[i]
                Q = np.array(self.Q[2:4, 2:4])
                F = np.array(self.F[2:4, 2:4])

            if np.shape(p2_[i])[0] == 4:
                p2 = p2_[i][2:4, 2:4]
                K2 = K2_[i][2:4, 2:4]
                K1 = np.array(self.K[i])

            if np.shape(s1[i])[0] == 4:
                ss1 = s1[i][2:4]
            else:
                ss1 = s1[i]

            if np.shape(s2[i])[0] == 4:
                ss2 = s2[i][2:4]
            else:
                ss2 = s2[i]

            dx = ss1 - ss2

            # cross-covariance terms
            cross_cov = np.matmul((np.eye(2) - K1), np.matmul(np.matmul(F, cross_cov_prev), F.T), (np.eye(2) - K2)) + \
                        np.matmul(np.matmul((np.eye(2) - K1), Q), (np.eye(2) - K2))
            cross_cov_prev = cross_cov
            # P_i + P_j  - P_ij - P_ji
            dist_cc += np.matmul(dx.T, np.matmul(scipy.linalg.inv(p1 + p2 - cross_cov - cross_cov), dx))
        return dist_cc

    def step(self):
        m, _ = self.get_latest_message()

        x_k_bar = np.matmul(self.F, self.x_k[-1]) + np.matmul(self.Q, np.random.normal(size=self.sensor_kf.state_dim))
        # state covariance prediction
        self.P.append(np.matmul(self.F, np.matmul(self.P[-1], self.F.T)) + self.Q)
        # measurement prediction
        self.y_k.append(x_k_bar + np.matmul(self.R, np.random.normal(size=self.sensor_kf.state_dim)))
        # innovation
        # if no new measurements, e_k is 0.
        e_k = (m - self.y_k[-1]) if m is not None else np.zeros([self.sensor_kf.state_dim])

        # K_k = P * inv(P + R)
        u = scipy.linalg.inv(self.P[-1] + self.R)
        self.K.append(np.matmul(self.P[-1], u))
        # l = scipy.linalg.cho_factor(self.P + self.R)
        # u = scipy.linalg.cho_solve(l, np.eye(4))
        # K_k = np.matmul(self.P, scipy.linalg.solve(l[0].T, u, sym_pos=True, lower=True))
        # state update
        self.x_k.append(x_k_bar + np.matmul(self.K[-1], e_k))
        # covariance update
        self.P[-1] -= np.matmul(self.K[-1], self.P[-1])

        if not np.all(np.diagonal(self.P[-1]) >= 0.):
            print("  [!] State covariance no longer positive semi-definite!")
            print("{}".format(self.P[-1]))
