import numpy as np
import utm


class FusedTrackCfg:
    # TODO
    def __init__(self, dt):
        self.z = 3.49  # z-score corresponding to 95 %
        self.dt = dt
        # should cover the min and max acceleration of any vehicle
        # that will be tracked
        # max accel is +- 3 m/s^2
        self.accel = 4  # m/s^2
        # variance of the noice process that models the acceleration
        sigma_a = self.accel / self.z

        # Process noise covariance
        # TODO: test other dynamics models
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

    @staticmethod
    def parse_msg(msg):
        """
        Extract the values needed to run a Kalman Filter
        :param msg:
        :return: measurement [x, xdot, y, ydot]
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