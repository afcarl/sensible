from __future__ import division

from sensible.tracking.state_estimator import StateEstimator
from sensible.tracking.dsrc_track_cfg import DSRCTrackCfg

import numpy as np
import scipy.linalg
import scipy.optimize as opt


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """
    def __init__(self, sensor_kf, use_cov_intersection=False):
        super(KalmanFilter, self).__init__(use_cov_intersection)
        self.Q = sensor_kf.Q
        self.P = sensor_kf.P
        self.F = sensor_kf.F
        self.R = sensor_kf.R

        self.sensor_kf = sensor_kf

    def use_cov_intersection(self, val):
        # covariance intersection only supported for DSRC sensor
        if val:
            assert self.sensor_kf == DSRCTrackCfg, "  [!] covariance intersection is only supported for DSRC currently"
        self._use_cov_intersection = val

    def parse_msg(self, msg):
        return self.sensor_kf.parse_msg(msg)

    def measurement_residual_covariance(self):
        return self.P + self.R

    def process_covariance(self):
        return self.P

    def step(self):

        m, _ = self.get_latest_message()

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

        if not np.all(self.P >= 0.):
            print("  [Warning] state covariance no longer positive definite!")

        #print("  [*] Kalman step {}".format(self.k))

    def covariance_intersection(self, b_bar, P_b_bar):
        """
        Append a fused estimate of the states from two sensors A and B to x_k_fused.
        If not using the covariance intersection algorithm, should append a blank entry
        so x_k_fused and x_k track eachother.

        :param b_bar:
        :param P_b_bar:
        :return:
        """
        if not self.use_cov_intersection:
            self.x_k_fused.append(None)
            assert len(self.x_k) == len(self.x_k_fused)
            return

        P_a_inv = scipy.linalg.inv(self.P[2:4, 2:4])
        P_b_inv = scipy.linalg.inv(P_b_bar)

        # solve for optimal combination parameters
        # the objective function is the determinant (or trace?) of the inverse of the
        # convex combination of the information (inverse cov) from state estimates from
        # the two sensors
        res = opt.minimize(lambda x: scipy.linalg.det(scipy.linalg.inv(x[0] * P_a_inv + (1. - x[0]) * P_b_inv)),
                     x0=np.array([0.5]),
                     method='BFGS',
                     constraints=({'type': 'ineq', 'fun': lambda x: x[0]},  # x >= 0
                                  {'type': 'ineq', 'fun': lambda x: 1 - x[0]}))  # 1 - x >= 0 == x <= 1

        w = res.x[0]
        P_opt_inv = np.zeros((4, 4))
        P_opt_inv[2:4, 2:4] = w * P_a_inv + (1. - w[0]) * P_b_inv
        P_opt_inv[0:2, 0:2] = self.P[0:2, 0:2]

        self.x_k_fused.append(w * P_a_inv * self.x_k[self.k] + (1. - w) * P_b_inv * b_bar)

        # for debugging
        return P_a_inv, P_b_inv, P_opt_inv, self.x_k[self.k], b_bar, self.x_k_fused[self.k]