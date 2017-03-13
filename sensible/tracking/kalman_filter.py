from __future__ import division
from sensible.tracking.state_estimator import StateEstimator
import utm
import numpy as np


class KalmanFilter(StateEstimator):
    """
    A linear Gaussian Kalman Filter for tracking
    vehicles following a standard constant velocity model.
    """
    def __init__(self, dt):
        super(KalmanFilter, self).__init__()
        self.z = 3.49
        self.dt = dt
        # should cover the min and max acceleration of any vehicle
        # that will be tracked
        self.accel = 3  # m/s^2
        # variance of the noice process that models the acceleration
        sigma_a = self.accel / self.z

        # Process noise covariance
        self.Q = np.multiply(np.power(sigma_a, 2),
                             np.array([[(np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2), 0, 0],
                                       [(np.power(self.dt, 3) / 2), np.power(self.dt, 2), 0, 0],
                                       [0, 0, (np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2)],
                                       [0, 0, (np.power(self.dt, 3) / 2), np.power(self.dt, 2)]]))

        # variance of a gaussian distribution over a position (x,y) meters corresponding to += 1.5 m
        sigma_1 = 0.4417
        # variance corresponding to a standard normal (+= 1 m)
        sigma_2 = 1 / self.z

        # measurement covariance
        self.R = np.eye(4)
        self.R[0][0] = np.power(sigma_1, 2)
        self.R[1][1] = np.power(sigma_1, 2)
        self.R[2][2] = np.power(sigma_2, 2)
        self.R[3][3] = np.power(sigma_2, 2)

        # Dynamics
        self.F = np.eye(4)
        self.F[0][1] = -self.dt
        self.F[2][3] = self.dt

        # initial state covariance
        self.P = np.eye(4)

    def parse_msg(self, msg):
        """
        Extract the values needed to run the Kalman Filter
        :param msg:
        :return:
        """
        x_hat, y_hat, zone_num, zone_letter = utm.from_latlon(msg['lat'], msg['lon'])
        heading = msg['heading']

        if heading >= 0 or heading <= 180:
            heading -= 90.0
        else:
            heading -= 180.0

        # heading is degrees counter-clockwise from true north, so we
        # need to subtract another 180
        x_hat_dot = msg['speed'] * np.cos(np.deg2rad(heading - 180.0))
        y_hat_dot = msg['speed'] * np.sin(np.deg2rad(heading - 180.0))

        return np.array([x_hat, x_hat_dot, y_hat, y_hat_dot])

    def step(self):
        m = self.get_latest_measurement()

        # No measurements available
        if m is None:
            print("  [Kalman Filter] No measurements available")
            return

        # First measurement
        if self.k == 0:
            self.x_k[self.k] = m
        else:
            # self.k > 0
            x_k_bar = np.matmul(self.F, self.x_k[self.k - 1]) + np.matmul(self.Q, np.random.normal(size=(4, 1)))
            # state covariance prediction
            self.P = np.matmul(self.F, np.matmul(self.P, self.F.T)) + self.Q
            # measurement prediction
            y_k_bar = x_k_bar + np.matmul(self.R, np.random.normal(size=(4, 1)))
            # innovation
            e_k = m - y_k_bar

            # Compute Cholesky Factorization
            L = np.linalg.cholesky(self.P + self.R)



        self.k += 1
