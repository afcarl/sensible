from sensible.tracking.state_estimator import StateEstimator

import numpy as np
import scipy.linalg


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """
    def __init__(self, sensor_kf, fused_track=False):
        super(KalmanFilter, self).__init__(fused_track, sensor_kf.stationary_R)
        self.Q = sensor_kf.Q
        self.P = sensor_kf.P
        self.F = sensor_kf.F
        self.R = sensor_kf.R
        self.sensor_kf = sensor_kf
        self.K = None

    def parse_msg(self, msg, stationary_R=True):
        return self.sensor_kf.parse_msg(msg, stationary_R)

    def measurement_residual_covariance(self):
        return self.P + self.R

    def process_covariance(self):
        return self.P

    def update_measurement_covariance(self, x_rms, y_rms):
        self.R = self.sensor_kf.update_measurement_covariance(x_rms, y_rms)

    def mahalanobis_(self, s1, p1, s2, p2, K):

        if np.shape(p1)[0] == 4:
            p1 = p1[2:4, 2:4]

        if np.shape(p2)[0] == 4:
            p2 = p2[2:4, 2:4]

        if np.shape(s1)[0] == 4:
            s1 = s1[2:4]

        if np.shape(s2)[0] == 4:
            s2 = s2[2:4]

        dx = s1 - s2
        # cross-covariance terms
        p3 = (np.eye(2) - self.K) * self.Q * (np.eye(2) - K)
        # P_i + P_j  - P_ij - P_ji
        return np.matmul(dx.T, np.matmul(scipy.linalg.inv(p1 + p2 - p3 - p3), dx))

    def step(self):
        m, _ = self.get_latest_message()

        x_k_bar = np.matmul(self.F, self.x_k[-1]) + np.matmul(self.Q, np.random.normal(size=self.sensor_kf.state_dim))
        # state covariance prediction
        self.P = np.matmul(self.F, np.matmul(self.P, self.F.T)) + self.Q
        # measurement prediction
        self.y_k.append(x_k_bar + np.matmul(self.R, np.random.normal(size=self.sensor_kf.state_dim)))
        # innovation
        # if no new measurements, e_k is 0.
        e_k = (m - self.y_k[-1]) if m is not None else np.zeros([self.sensor_kf.state_dim])

        # K_k = P * inv(P + R)
        u = scipy.linalg.inv(self.P + self.R)
        self.K = np.matmul(self.P, u)
        # l = scipy.linalg.cho_factor(self.P + self.R)
        # u = scipy.linalg.cho_solve(l, np.eye(4))
        # K_k = np.matmul(self.P, scipy.linalg.solve(l[0].T, u, sym_pos=True, lower=True))
        # state update
        self.x_k.append(x_k_bar + np.matmul(self.K, e_k))
        # covariance update
        self.P -= np.matmul(self.K, self.P)

        if not np.all(np.diagonal(self.P) >= 0.):
            print("  [!] State covariance no longer positive semi-definite!")
            print("{}".format(self.P))
