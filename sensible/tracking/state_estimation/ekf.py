import numpy as np
from kalman_filter import KalmanFilter


class ExtendedKalmanFilter(KalmanFilter):
    """
    An EKF used for tracking vehicles. Can be configured 
    for any sensor given a configuration class "ekf_config".
    """

    def __init__(self, ekf_config, sliding_window, fused_track=False):
        super(ExtendedKalmanFilter, self).__init__(ekf_config, sliding_window, fused_track)

    def step(self):
        m, _ = self.get_latest_message()

        x_k_bar = np.matmul(self.F, self.x_k[-1]) + np.matmul(self.Q, np.random.normal(size=self.kf_config.state_dim))
        self.P.append(np.matmul(self.F, np.matmul(self.P[-1], self.F.T)) + self.Q)

        # nonlinear measurement update
        # compute prediction h(x_k|x_k-1)
        x = self.x_k_bar[-1][0]
        y = self.x_k_bar[-1][2]
        x_dot = self.x_k_bar[-1][1]
        y_dot = self.x_k_bar[-1][3]
        theta_pred = np.arctan2(y_dot, x_dot) 
        h = np.array([x, y, x_dot / np.cos(theta_pred), theta_pred])
        # jacobian of h evaluated at x_k_bar
        c = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0],
                     [0, 0, 1 / np.cos(theta_pred), 0]
                     [0, 0, -y_dot/(x_dot ** 2 * ((y_dot ** 2 / x_dot ** 2 ) + 1)),
                         1 / (x_dot * ((y_dot ** 2 / x_dot ** 2 ) + 1))]])

        # measurement prediction
        self.y_k.append(h + np.matmul(self.R, np.random.normal(size=self.kf_config.state_dim)))

        # innovation
        e_k = (m - self.y_k[-1]) if m is not None else np.zeros([self.kf_config.state_dim])

        # Kalman Gain
        u = scipy.linalg.inv(np.matmul(np.matmul(c, self.P[-1]), c.T) + self.R)
        self.K.append(np.matmul(self.P[-1], np.matmul(c, u)))

        # state update
        self.x_k.append(x_k_bar + np.matmul(self.K[-1], e_k))
        # covariance update
        self.P[-1] -= np.matmul(np.matmul(self.K[-1], c), self.P[-1])

        # divergence check
        if not np.all(np.diagonal(self.P[-1] >= 0.):
            print('  [!] State covariance no longer positive semi-definite!')
        print('{}'.format(self.P[-1]))
