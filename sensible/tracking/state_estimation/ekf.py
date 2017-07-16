import numpy as np
import scipy.linalg
from kalman_filter import KalmanFilter


class ExtendedKalmanFilter(KalmanFilter):
    """
    An EKF used for tracking vehicles. Can be configured 
    for any sensor given a configuration class "ekf_config".
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

        x_k_bar = np.matmul(self.F, self.x_k[-1]) + np.matmul(self.Q, np.random.normal(size=self.sensor_cfg.state_dim))
        self.P.append(np.matmul(self.F, np.matmul(self.P[-1], self.F.T)) + self.Q)

        # nonlinear measurement update
        # compute prediction h(x_k|x_k-1)
        if self.sensor_cfg.motion_model == 'CV':
            x = x_k_bar[0]
            y = x_k_bar[2]
            x_dot = x_k_bar[1]
            y_dot = x_k_bar[3]
            theta_pred = np.arctan2(y_dot, x_dot)
            h = np.array([x, y, x_dot / np.cos(theta_pred), np.rad2deg(theta_pred)])
            # jacobian of h evaluated at x_k_bar
            c = np.array([[1, 0, 0, 0],
                         [0, 0, 1, 0],
                         [0, (np.sqrt((y_dot ** 2 / x_dot ** 2)) + 1) - y_dot ** 2 /
                          (x_dot ** 2 * (np.sqrt((y_dot ** 2 / x_dot ** 2)) + 1)),
                          0, y_dot / (x_dot ** 2 * (np.sqrt((y_dot ** 2 / x_dot ** 2)) + 1))],
                         [0, -y_dot/(x_dot ** 2 * ((y_dot ** 2 / x_dot ** 2) + 1)),
                             0, 1 / (x_dot * ((y_dot ** 2 / x_dot ** 2) + 1))]])
        elif self.sensor_cfg.motion_model == 'CA':
            x = x_k_bar[0]
            y = x_k_bar[3]
            x_dot = x_k_bar[1]
            y_dot = x_k_bar[4]
            x_ddot = x_k_bar[2]
            y_ddot = x_k_bar[5]
            theta_pred = np.arctan2(y_dot, x_dot)
            h = np.array([x, y, x_dot / np.cos(theta_pred), np.rad2deg(theta_pred)])
            # jacobian of h evaluated at x_k_bar
            c = np.array([[1, 0, 0, 0, 0, 0],
                          [0, 0, 0, 1, 0, 0],
                          [0, 1 / np.cos(theta_pred), 0, 0, 0, 0],
                          [0, -y_dot / (x_dot ** 2 * ((y_dot ** 2 / x_dot ** 2) + 1)), 0, 0,
                           1 / (x_dot * ((y_dot ** 2 / x_dot ** 2) + 1)), 0]])
        # measurement prediction
        self.y_k.append(h + np.matmul(self.R, np.random.normal(size=self.sensor_cfg.state_dim)))

        # innovation
        e_k = (m - self.y_k[-1]) if m is not None else np.zeros([self.sensor_cfg.state_dim])

        # Kalman Gain
        u = scipy.linalg.inv(np.matmul(np.matmul(c, self.P[-1]), c.T) + self.R)
        self.K.append(np.matmul(self.P[-1], np.matmul(c.T, u)))

        # state update
        self.x_k.append(x_k_bar + np.matmul(self.K[-1], e_k))
        # covariance update
        self.P[-1] -= np.matmul(np.matmul(self.K[-1], c), self.P[-1])

        print('Step: ')
        print('innovation: {}'.format(e_k))
        print('kalman gain: {}'.format(self.K[-1]))
        print('covariance: {}'.format(self.P[-1]))

        # divergence check
        if not np.all(np.diagonal(self.P[-1] >= 0.)):
            print('  [!] State covariance no longer positive semi-definite!')
            print('{}'.format(self.P[-1]))
