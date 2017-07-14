import numpy as np
import utm


class DSRCTrackCfg:

    def __init__(self, dt, motion_model='CV'):
	"""
	x_k = [x (UTM Easting), x_dot, x_double_dot, y (UTM Northing), y_dot, y_double_dot]
	y_k = [x (UTM Easting), y (UTM Northing), v, theta]

	Motion models: 
		1. CV: constant velocity
		2. CA: constant acceleration
	"""
        self.z = 3.49  # z-score corresponding to 95 %
        self.dt = dt
        self.state_dim = 4
        self.stationary_R = False

        # should cover the min and max acceleration of any vehicle
        # that will be tracked
        # max accel is +- 3 m/s^2
        self.accel = 4  # m/s^2
        # variance of the noice process that models the acceleration
        sigma_a = self.accel / self.z

        # std dev of a gaussian distribution over a position (x,y) meters corresponding to += 4 m
        # TODO: try 2 ?
        sigma_1 = 4 / self.z
        # std dev corresponding to a standard normal (+= 1 m/s)
        sigma_2 = 2 / self.z

        # measurement covariance
        self.R = np.eye(self.state_dim)
        self.R[0][0] = sigma_1 ** 2  # x
        self.R[1][1] = sigma_2 ** 2  # x dot
        self.R[2][2] = sigma_1 ** 2  # y
        self.R[3][3] = sigma_2 ** 2  # y dot

        # initial state covariance
        self.P = np.eye(self.state_dim)

	if motion_model == 'CV': 
	    mm = self.constant_velocity
	else:
	    print('Unsupported state estimation motion model: {}'.format(motion_model))
	    exit(1)

	self.F, self.Q = mm()

def constant_velocity(self):
        # Dynamics
        F = np.eye(self.state_dim)
        F[0][1] = -self.dt
        F[2][3] = self.dt

        # Process noise covariance
        Q = np.multiply(np.power(sigma_a, 2),
		     np.array([[(np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2), 0, 0],
			       [(np.power(self.dt, 3) / 2), np.power(self.dt, 2), 0, 0],
			       [0, 0, (np.power(self.dt, 4) / 4), (np.power(self.dt, 3) / 2)],
			       [0, 0, (np.power(self.dt, 3) / 2), np.power(self.dt, 2)]]))
	return F, Q

    def update_measurement_covariance(self, x_rms, y_rms):
        self.R[0][0] = (x_rms / self.z) ** 2
        self.R[2][2] = (y_rms / self.z) ** 2
        return self.R

    @staticmethod
    def parse_msg(msg, state_estimation='kf', stationary_R=False):
        """
        Extract the values needed to run a Kalman Filter
        :param msg:
        :return: measurement [x, xdot, y, ydot]
        """
	if state_estimation == 'kf':
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
		measurement = np.array([x_hat, x_hat_dot, y_hat, y_hat_dot])
	elif state_estimation == 'ekf' or state_estimation == 'pf':
		heading = msg['heading']

		if heading >= 0 or heading <= 180:
		    heading -= 90.0
		else:
		    heading -= 180.0
		
		measurement = np.array([msg['lat'], msg['lon'], msg['speed'], heading])

        x_rms = msg['rms_lat']
        y_rms = msg['rms_lon']

        if not stationary_R:
            return measurement, x_rms, y_rms
        else:
            return measurement
