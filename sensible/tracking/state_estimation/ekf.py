from __future__ import absolute_import

import numpy as np
import scipy.linalg

from .kalman_filter import KalmanFilter


class ExtendedKalmanFilter(KalmanFilter):
    """
    An EKF used for tracking vehicles. Can be configured 
    for any sensor given a configuration class "ekf_config".

    Need more data of the vehicle driving at different orientations. Seems to be
    the case that the measurement error increases into a long-tailed exponential distribution
    in the direction of motion. Need to check when driving SW,NE,NW,SE.

    WE don't make assumptions about the physical characteristics of the vehicle
    to make our system general for tracking vehicles at intersections; hence,
    we capture the vehicle dynamics via the measurement uncertainty that
    is dependent on the state

    """

    def __init__(self, ekf_config, sliding_window, use_bias_estimation, fused_track=False):
        super(ExtendedKalmanFilter, self).__init__(ekf_config, sliding_window,
                                                   use_bias_estimation, fused_track)

    def step(self):
        if len(self.x_k) < 1:
            return
        elif self.no_step:
            self.no_step = False
            return

        m, _ = self.get_latest_message()

        if m is not None and self.use_bias_estimation:
            bias_estimate = self.sensor_cfg.bias_estimate(m[2], np.deg2rad(m[3]))
            m[0:2] += bias_estimate

        if m is not None and abs(m[2]) < 0.8:
            if len(self.K) == 0:
                return
            self.x_k.append(self.x_k[-1])
            self.P.append(self.P[-1])
            self.K.append(self.K[-1])
            self.y_k.append(self.y_k[-1])
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
        deg_pred = np.rad2deg(theta_pred)
        
        h = np.array([x, y, np.sqrt(x_dot ** 2 + y_dot ** 2), deg_pred])

        # jacobian of h evaluated at x_k_bar 
        if self.sensor_cfg.motion_model == 'CV':
            c = np.array([[1, 0, 0, 0],
                          [0, 0, 1, 0],
                          [0, x_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2)),
                           0, y_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2))],
                          [0, np.rad2deg(-y_dot / (x_dot ** 2 + y_dot ** 2)),
                              0, np.rad2deg(x_dot / (x_dot ** 2 + y_dot ** 2))]])
        elif self.sensor_cfg.motion_model == 'CA':
            # jacobian of h evaluated at x_k_bar
            c = np.array([[1, 0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0, 0],
                          [0, x_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2)), 0,
                           0, y_dot / (np.sqrt(x_dot ** 2 + y_dot ** 2)), 0],
                          [0, np.rad2deg(-y_dot / (x_dot ** 2 + y_dot ** 2)), 0,
                              0, np.rad2deg(x_dot / (x_dot ** 2 + y_dot ** 2)), 0]])

        #R = self.sensor_cfg.rotate_covariance(theta_pred)
        R = self.sensor_cfg.R
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
