from __future__ import division

from sensible.tracking.state_estimator import StateEstimator

import numpy as np
import scipy.linalg


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """
    def __init__(self, dt):
        super(KalmanFilter, self).__init__()
        self.z = 3.49  # z-score corresponding to 95 %
        self.dt = dt
        # should cover the min and max acceleration of any vehicle
        # that will be tracked
        # max accel is +- 3 m/s^2
        self.accel = 4  # m/s^2
        # variance of the noice process that models the acceleration
        sigma_a = self.accel / self.z

        # Process noise covariance
        self.Q = np.multiply(np.power(sigma_a, 2),
                             np.array([[(np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2), 0, 0],
                                       [(np.power(self.dt, 3) / 2), np.power(self.dt, 2), 0, 0],
                                       [0, 0, (np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2)],
                                       [0, 0, (np.power(self.dt, 3) / 2), np.power(self.dt, 2)]]))

        # TODO: increase this variance to about +- 3 m
        # variance of a gaussian distribution over a position (x,y) meters corresponding to += 1.5 m
        sigma_1 = 3 / self.z
        # variance corresponding to a standard normal (+= 1 m)
        sigma_2 = 1 / self.z

        # measurement covariance
        self.R = np.eye(4)
        self.R[0][0] = np.power(sigma_1, 2)
        self.R[2][2] = np.power(sigma_1, 2)
        self.R[1][1] = np.power(sigma_2, 2)
        self.R[3][3] = np.power(sigma_2, 2)

        # Dynamics
        self.F = np.eye(4)
        self.F[0][1] = -self.dt
        self.F[2][3] = self.dt

        # initial state covariance
        self.P = np.eye(4)

    def measurement_residual_covariance(self):
        return self.P + self.R

    def step(self):

        m, _ = self.get_latest_measurement()

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
