import numpy as np
import utm

#radar_lat = 29.6216931
#radar_lon = -82.3867591
# compute UTM coordinates of the radar
#utm_n, utm_e, zone, letter = \
#            utm.from_latlon(radar_lat, radar_lon)


class RadarTrackCfg:

    def __init__(self, dt, motion_model):
        self.dt = dt
        self.state_dim = 2
        self.measurement_dim = 2
        self.stationary_R = True
        self.motion_model = motion_model

        # should cover the min and max acceleration of any vehicle
        # standard deviation of the noice process that models the acceleration
        self.accel_std_dev = 3

        # standard deviation of range estimate
        sigma_1 = 1.5  # 1 std dev
        # standard deviation corresponding to a standard normal
        sigma_2 = 0.25  # 1 std dev

        # measurement covariance
        self.R = np.eye(self.state_dim)
        self.R[0][0] = sigma_1 ** 2
        self.R[1][1] = sigma_2 ** 2

        # initial state covariance
        self.P = np.eye(self.state_dim)

        self.F, self.Q, self.init_state = self.constant_velocity()

    @staticmethod
    def parse_msg(msg, stationary_R):
        """
        Extract the values needed to run a Kalman Filter
        :param msg:
        :return: measurement [y, ydot]
        """
        return np.array([msg['yPos'], msg['speed']])
    
    def constant_velocity(self):
        # Kinematics
        F = np.eye(self.state_dim)
        F[0][1] = self.dt
        # Process noise covariance
        # Test other kinematics models
        Q = np.multiply(self.accel_std_dev ** 2,
                             np.array([[(self.dt ** 4) / 4, (self.dt ** 3) / 2],
                                       [(self.dt ** 3) / 2, self.dt ** 2]]))
        
        def init_state(y_k, y_k_prev, dt):
            """ [x, xdot = vcos(theta), y, ydot = vsin(theta)] """
            return y_k

        return F, Q, init_state