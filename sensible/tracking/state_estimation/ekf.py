from __future__ import absolute_import

import numpy as np
import scipy.linalg

from .kalman_filter import KalmanFilter


class ExtendedKalmanFilter(KalmanFilter):
    """
    An EKF used for tracking vehicles. Can be configured 
    for any sensor given a configuration class "ekf_config".

    Measurement error estimation:

    Gaussian with parameters

    UTM Northing (meters)
    ('mu: ', -2.1352512520508538)
    ('var: ', 1.8515957687696858)

    UTM Easting (meters)
    ('mu: ', 0.2821831424596038)
    ('var: ', 0.28342931177253217)

    heading (degrees)
    ('mu: ', -0.055275516593625479)
    ('var: ', 0.045582569132330331)


    Need more data of the vehicle driving at different orientations. Seems to be
    the case that the measurement error increases into a long-tailed exponential distribution
    in the direction of motion. Need to check when driving SW,NE,NW,SE.

    WE don't make assumptions about the physical characteristics of the vehicle
    to make our system general for tracking vehicles at intersections; hence,
    we capture the vehicle dynamics via the measurement uncertainty that
    is dependent on the state

    """

    def __init__(self, ekf_config, sliding_window, fused_track=False):
        super(ExtendedKalmanFilter, self).__init__(ekf_config, sliding_window, fused_track)

    def step(self):
        if len(self.x_k) < 1:
            return
        elif self.no_step:
            self.no_step = False
            return

        m, _ = self.get_latest_message()

        bias_estimate = self.sensor_cfg.bias_estimate(m[2], np.deg2rad(m[3]))
        m[0:2] -= bias_estimate

        # if the speed is 0, just set the message as the state
        if m[2] == 0.0:
            if self.sensor_cfg.motion_model == 'CV':
                self.x_k.append(np.array([m[0], 0.0, m[1]], 0.0))
            else:
                self.x_k.append(np.array([m[0], 0.0, 0.0, m[1], 0.0, 0.0]))
            self.P.append(self.P[-1])
            self.K.append(self.K[-1])
            self.y_k.append(None)
            return

        x_k_bar = np.matmul(self.F, self.x_k[-1]) + np.matmul(self.Q, np.random.normal(size=self.sensor_cfg.state_dim))
        self.P.append(np.matmul(self.F, np.matmul(self.P[-1], self.F.T)) + self.Q)

        # nonlinear measurement update
        # compute prediction h(x_k|x_k-1)
        if self.sensor_cfg.motion_model == 'CV':
            x = x_k_bar[0]
            y = x_k_bar[2]
            x_dot = x_k_bar[1]
            y_dot = x_k_bar[3]
        elif self.sensor_cfg.motion_model == 'CA':
            x = x_k_bar[0]
            y = x_k_bar[3]
            x_dot = x_k_bar[1]
            y_dot = x_k_bar[4]

        theta_pred = np.arctan2(y_dot, x_dot)
        if theta_pred < 0:
            theta_pred += 2 * np.pi
        h = np.array([x, y, np.sqrt(x_dot ** 2 + y_dot ** 2), np.rad2deg(theta_pred)])

        # jacobian of h evaluated at x_k_bar 
        if self.sensor_cfg.motion_model == 'CV':
            c = np.array([[1, 0, 0, 0],
                          [0, 0, 1, 0],
                          [0, x_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2)),
                           0, y_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2))],
                          [0, np.rad2deg(-y_dot / (x_dot ** 2 * ((y_dot ** 2 / x_dot ** 2) + 1))),
                           0, np.rad2deg(1 / (x_dot * ((y_dot ** 2 / x_dot ** 2) + 1)))]])
        elif self.sensor_cfg.motion_model == 'CA':
            # jacobian of h evaluated at x_k_bar
            c = np.array([[1, 0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0, 0],
                          [0, x_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2)), 0,
                           0, y_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2)), 0],
                          [0, np.rad2deg(-y_dot / (x_dot ** 2 * ((y_dot ** 2 / x_dot ** 2) + 1))), 0,
                           0, np.rad2deg(1 / (x_dot * ((y_dot ** 2 / x_dot ** 2) + 1))), 0]])

        R = self.sensor_cfg.rotate_covariance(theta_pred)
        # measurement prediction
        self.y_k.append(h + np.matmul(R, np.random.normal(size=self.sensor_cfg.measurement_dim)))

        # innovation
        e_k = (m - self.y_k[-1]) if m is not None else np.zeros([self.sensor_cfg.measurement_dim])

        # Kalman Gain
        u = scipy.linalg.inv(np.matmul(np.matmul(c, self.P[-1]), c.T) + R)
        self.K.append(np.matmul(self.P[-1], np.matmul(c.T, u)))

        # state update
        self.x_k.append(x_k_bar + np.matmul(self.K[-1], e_k))
        # covariance update
        self.P[-1] = np.matmul(np.eye(self.sensor_cfg.state_dim) - np.matmul(self.K[-1], c), self.P[-1])

        # divergence check
        if not np.all(np.diagonal(self.P[-1] >= 0.)):
            print('  [!] State covariance no longer positive semi-definite!')
            print('{}'.format(self.P[-1]))
