import numpy as np
import utm


class DSRCTrackCfg:
    def __init__(self, dt, motion_model='CV'):
        """
        For CA:
            x_k = [x (UTM Easting), x_dot, x_double_dot, y (UTM Northing), y_dot, y_double_dot]
        For CV: 
            x_k = [x, x_dot, y, y_dot]

        y_k = [x (UTM Easting), y (UTM Northing), v, theta]
        
        The assumption made is that the GPS has been locally transformed 
        to a standard location on the vehicle, such as the center
        of the front bumper.

        Motion models:
            1. CV: constant velocity
            2. CA: constant acceleration
        """
        self.z = 3.49  # z-score corresponding to 95 %
        self.dt = dt
        self.stationary_R = False

        ### SET MEASUREMENT UNCERTAINTY PARAMETERS HERE ###

        # std dev of a gaussian distribution over a position (x,y) meters
        # corresponding to +- m
        utm_easting_std_dev = 1 / self.z
        utm_northing_std_dev = 2.2 / self.z
        # std dev corresponding to a standard normal (+- m/s)
        speed_std_dev = 1 / self.z
        # std dev heading in degrees, (+- deg)
        heading_std_dev = 0.1 / self.z

        self.motion_model = motion_model

        if motion_model == 'CV':
            mm = self.constant_velocity
            self.accel_std_dev = 4 / self.z # (+- m/s^2)
            self.state_dim = 4

        elif motion_model == 'CA':
            mm = self.constant_acceleration
            self.state_dim = 6
        else:
            print('Unsupported state estimation motion model: {}'.format(motion_model))
            exit(1)

        self.F, self.Q, self.init_state = mm()

        # measurement covariance
        self.R = np.eye(self.state_dim)
        self.R[0][0] = utm_easting_std_dev ** 2  # x
        self.R[1][1] = utm_northing_std_dev ** 2  # y
        self.R[2][2] = speed_std_dev ** 2  # v
        self.R[3][3] = heading_std_dev ** 2  # heading

        # initial state covariance
        self.P = np.eye(self.state_dim)

    def constant_velocity(self):
        # Dynamics
        F = np.eye(self.state_dim)
        F[0][1] = self.dt
        F[2][3] = -self.dt

        # Process noise covariance
        Q = np.multiply(self.accel_std_dev ** 2,
                        np.array([[(np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2), 0, 0],
                                  [(np.power(self.dt, 3) / 2), np.power(self.dt, 2), 0, 0],
                                  [0, 0, (np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2)],
                                  [0, 0, (np.power(self.dt, 3) / 2), np.power(self.dt, 2)]]))

        def init_state(y_k, y_k_prev, dt):
            """ [x, xdot = vcos(theta), y, ydot = vsin(theta)] """
            return np.array([y_k[0], y_k[2] * np.cos(np.deg2rad(y_k[3])),
                             y_k[1], y_k[2] * np.sin(np.deg2rad(y_k[3]))])
        return F, Q, init_state

    def constant_acceleration(self):
        # Dynamics
        F = np.eye(self.state_dim)
        F[0][1] = self.dt
        F[0][2] = (self.dt ** 2) / 2
        F[1][2] = -self.dt
        F[3][4] = self.dt
        F[3][5] = (self.dt ** 2) / 2
        F[4][5] = self.dt

        # TODO: Check Blackmon pg. 207
        Q = (self.accel_std_dev ** 2) * np.array([
            [self.dt ** 5 / 20, self.dt ** 4 / 8, self.dt ** 3 / 6, 0, 0, 0],
            [self.dt ** 4 / 8, self.dt ** 3 / 3, self.dt ** 2 / 2, 0, 0, 0],
            [self.dt ** 3 / 6, self.dt ** 2 / 2, self.dt, 0, 0, 0],
            [0, 0, 0, self.dt ** 5 / 20, self.dt ** 4 / 8, self.dt ** 3 / 6],
            [0, 0, 0, self.dt ** 4 / 8, self.dt ** 3 / 3, self.dt ** 2 / 2],
            [0, 0, 0, self.dt ** 3 / 6, self.dt ** 2 / 2, self.dt]
        ])

        def init_state(y_k, y_k_prev, dt):
            """ [x, xdot, xddot, y, ydot, yddot] """
            xdot = y_k[2] * np.cos(np.deg2rad(y_k[3]))
            ydot = y_k[2] * np.sin(np.deg2rad(y_k[3]))
            xddot = (xdot - (y_k_prev[2] * np.cos(np.deg2rad(y_k[3])))) / dt
            yddot = (ydot - (y_k_prev[2] * np.sin(np.deg2rad(y_k[3])))) / dt

            return np.array([y_k[0], xdot, xddot,
                             y_k[1], ydot, yddot])
        return F, Q, init_state

    def update_measurement_covariance(self, x_rms, y_rms):
        self.R[0][0] = (x_rms / self.z) ** 2
        self.R[1][1] = (y_rms / self.z) ** 2
        return self.R

    @staticmethod
    def parse_msg(msg, stationary_R=False):
        """
        Construct a new measurement from a BSM

        :param msg:
        :return: measurement [x, y, v, theta]
        """
        x_hat, y_hat, zone_num, zone_letter = utm.from_latlon(msg['lat'], msg['lon'])

        heading = msg['heading']

        if heading >= 0 or heading <= 180:
            heading -= 90.0
        else:
            heading -= 180.0

        measurement = np.array([x_hat, y_hat, msg['speed'], heading])

        x_rms = msg['rms_lat']
        y_rms = msg['rms_lon']

        if not stationary_R:
            return measurement, x_rms, y_rms
        else:
            return measurement
