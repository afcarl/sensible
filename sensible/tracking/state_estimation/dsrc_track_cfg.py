import numpy as np
import utm


class DSRCTrackCfg:
    def __init__(self, dt, bias, motion_model='CV', spherical_R=False):
        """
        For CA:
            x_k = [x (UTM Easting), x_dot, x_double_dot, y (UTM Northing), y_dot, y_double_dot]
        For CV: 
            x_k = [x, x_dot, y, y_dot]

        y_k = [x (UTM Easting), y (UTM Northing), v, theta]
        
        The assumption made is that the GPS has been locally transformed 
        to a standard location on the vehicle, such as the center
        of the front bumper.

        For EKF - compute R as a function of the state; ellipse with major axis
        pointing in the direction of the heading & subtract away bias

        Motion models:
            1. CV: constant velocity
            2. CA: constant acceleration
        """
        self.dt = dt
        # TODO: don't accept RMS updates until this is fixed
        self.stationary_R = True
        self.measurement_dim = 4

        ### SET MEASUREMENT UNCERTAINTY PARAMETERS HERE ###

        # std dev of a gaussian distribution over a position (x,y) meters
        # corresponding to +- m
        # std dev corresponding to a standard normal (+- m/s)
        sigma_pos_max = 0.5  # 1.85  - high was 0.9 m low was 0.2
        sigma_pos_min = 0.25  # 0.51
        speed_std_dev = 0.1  # 0.25
        # std dev heading in degrees, (+- deg)
        # for EKF, set this to a much higher value (2-3 degrees?)
        heading_std_dev = 0.1
        
        self.bias_constant = bias  # default 0.167

        self.motion_model = motion_model
        
        if motion_model == 'CV':
            mm = self.constant_velocity
            self.accel_std_dev = 2  # (+- m/s^2)
            self.state_dim = 4

        elif motion_model == 'CA':
            mm = self.constant_acceleration
            self.state_dim = 6
        else:
            print('Unsupported state estimation motion model: {}'.format(motion_model))
            exit(1)

        self.F, self.Q, self.init_state = mm()

        # measurement covariance
        if not spherical_R:
            self.R = np.eye(self.measurement_dim)
            self.R[0][0] = sigma_pos_max ** 2  # x
            self.R[1][1] = sigma_pos_max ** 2  # y
            self.R[2][2] = speed_std_dev ** 2  # v
            self.R[3][3] = heading_std_dev ** 2  # heading
        else:
            self.R = np.eye(self.measurement_dim)
            self.R[0][0] = sigma_pos_max ** 2
            self.R[1][1] = speed_std_dev ** 2
            self.R[2][2] = sigma_pos_max ** 2
            self.R[3][3] = speed_std_dev ** 2

        # initial state covariance
        self.P = 10 * self.Q

    def constant_velocity(self):
        # Kinematics
        F = np.eye(self.state_dim)
        F[0][1] = self.dt
        F[2][3] = self.dt

        # Process noise covariance
        Q = np.multiply(self.accel_std_dev ** 2,
                        np.array([[self.dt ** 3 / 3, self.dt ** 2 / 2, 0, 0],
                                  [self.dt ** 2 / 2, self.dt, 0, 0],
                                  [0, 0, self.dt ** 3 / 3, self.dt ** 2 / 2],
                                  [0, 0, self.dt ** 2 / 2, self.dt]]))

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
        F[1][2] = self.dt
        F[3][4] = self.dt
        F[3][5] = (self.dt ** 2) / 2
        F[4][5] = self.dt

        Q = 1 * np.array([
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
            xddot = (xdot - (y_k_prev[2] * np.cos(np.deg2rad(y_k_prev[3])))) / dt
            yddot = (ydot - (y_k_prev[2] * np.sin(np.deg2rad(y_k_prev[3])))) / dt
            
            return np.array([y_k[0], xdot, xddot,
                             y_k[1], ydot, yddot])
        return F, Q, init_state

    def update_measurement_covariance(self, x_rms, y_rms):
        self.R[0][0] = x_rms ** 2
        self.R[1][1] = y_rms ** 2
        return self.R

    def rotate_covariance(self, theta):
        rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        R_bar = np.matmul(np.matmul(rot, self.R[0:2, 0:2]), rot.T)
        R = np.copy(self.R)
        R[0:2, 0:2] = R_bar
        return self.R

    def batch_rotate_covariance(self, theta):
        N = np.shape(theta)[0]
        rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        rr = np.matmul(rot.T, self.R[0:2, 0:2])
        R_bar = np.matmul(rr, np.transpose(rot, (1, 0, 2)).T)
        R = np.repeat(self.R.reshape(1, self.measurement_dim, self.measurement_dim), N, axis=0)
        R[:, 0:2, 0:2] = R_bar
        return R

    def bias_estimate(self, v, theta):
        return np.array([self.bias_constant * v * np.cos(theta), self.bias_constant * v * np.sin(theta)])

    @staticmethod
    def parse_msg(msg, stationary_R=False):
        """
        Construct a new measurement from a BSM

        :param msg:
        :return: measurement [x, y, v, theta]
        """
        x_hat, y_hat, zone_num, zone_letter = utm.from_latlon(msg['lat'], msg['lon'])

        heading = msg['heading']

        # convert from degrees from true north to
        # degrees from x axis (UTM easting)
        heading = (-heading + 90.) % 360.

        measurement = np.array([x_hat, y_hat, msg['speed'], heading])

        x_rms = msg['rms_lat']
        y_rms = msg['rms_lon']

        if not stationary_R:
            return measurement, x_rms, y_rms
        else:
            return measurement
