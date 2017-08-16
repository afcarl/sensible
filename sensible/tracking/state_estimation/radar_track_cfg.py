import numpy as np
import utm

#radar_lat = 29.6216931
#radar_lon = -82.3867591
# compute UTM coordinates of the radar
#utm_n, utm_e, zone, letter = \
#            utm.from_latlon(radar_lat, radar_lon)


class RadarTrackCfg:

    def __init__(self, dt):
        self.dt = dt
        self.state_dim = 2
        self.stationary_R = True

        # should cover the min and max acceleration of any vehicle
        # that will be tracked
        # max accel is +- 3 m/s^2
        self.accel = 4  # m/s^2
        # standard deviation of the noice process that models the acceleration
        sigma_a = self.accel

        # Process noise covariance
        # TODO: test other dynamics models
        self.Q = np.multiply(sigma_a ** 2,
                             np.array([[(self.dt ** 4) / 4, (self.dt ** 3) / 2],
                                       [(self.dt ** 3) / 2, self.dt ** 2]]))

        # standard deviation of range estimate
        sigma_1 = 3  # 1 std dev is +- 1.5 m
        # standard deviation corresponding to a standard normal
        sigma_2 = 0.5  # 1 std dev is +- 0.25 m/s

        # measurement covariance
        self.R = np.eye(self.state_dim)
        self.R[0][0] = sigma_1 ** 2
        self.R[1][1] = sigma_2 ** 2

        # Dynamics
        self.F = np.eye(self.state_dim)
        self.F[0][1] = self.dt

        # initial state covariance
        self.P = np.eye(self.state_dim)

    @staticmethod
    def parse_msg(msg, stationary_R):
        """
        Extract the values needed to run a Kalman Filter
        :param msg:
        :return: measurement [y, ydot]
        """
        return np.array([msg['yPos'], msg['speed']])
