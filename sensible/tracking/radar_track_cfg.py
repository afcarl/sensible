import numpy as np
import utm

radar_lat = 29.6216931
radar_lon = -82.3867591
# compute UTM coordinates of the radar
utm_n, utm_e, zone, letter = \
            utm.from_latlon(radar_lat, radar_lon)


class RadarTrackCfg:

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
        self.Q = np.multiply(sigma_a ** 2,
                             np.array([[(self.dt ** 4) / 4, (self.dt ** 3) / 2],
                                       [(self.dt ** 3) / 2, self.dt ** 2]]))

        # variance of a gaussian distribution over a position (x,y) meters corresponding to += 1.5 m
        sigma_1 = 3 / self.z  # position
        # variance corresponding to a standard normal
        sigma_2 = 0.28 / self.z  # speed

        # measurement covariance
        self.R = np.eye(2)
        self.R[0][0] = np.power(sigma_1, 2)
        self.R[1][1] = np.power(sigma_2, 2)

        # Dynamics
        self.F = np.eye(4)
        self.F[0][1] = -self.dt

        # initial state covariance
        self.P = np.eye(2)

    @staticmethod
    def parse_msg(msg):
        """
        Extract the values needed to run a Kalman Filter
        :param msg:
        :return: measurement [x, xdot, y, ydot]
        """
        # TODO: test
        # invert data to place in right coordinate frame
        y = msg['xPos'] + utm_n
        y_dot = msg['xVel']
        #x = -msg['yPos'] + utm_e
        #x_dot = msg['yVel']  # will be negative for vehicles approaching the intersection

        return np.array([y, y_dot])
