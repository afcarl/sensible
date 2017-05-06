from sensible.tracking.state_estimator import StateEstimator

import numpy as np
import scipy.linalg


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """
    def __init__(self, sensor_kf, fused_track=False):
        super(KalmanFilter, self).__init__(fused_track)
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
        K_k = np.matmul(self.P, u)
        # l = scipy.linalg.cho_factor(self.P + self.R)
        # u = scipy.linalg.cho_solve(l, np.eye(4))
        # K_k = np.matmul(self.P, scipy.linalg.solve(l[0].T, u, sym_pos=True, lower=True))
        # state update
        self.x_k.append(x_k_bar + np.matmul(K_k, e_k))
        # covariance update
        self.P -= np.matmul(K_k, self.P)

        if not np.all(np.diagonal(self.P) >= 0.):
            print("  [!] State covariance no longer positive definite!")
            print("{}".format(self.P))

        #print("  [*] Kalman step {}".format(self.k))