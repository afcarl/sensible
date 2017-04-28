import numpy as np

from sensible.tracking.track_state import TrackState
from sensible.tracking.kalman_filter import KalmanFilter
from sensible.sensors.DSRC import DSRC


class TrackType:
    CONNECTED = 1
    CONVENTIONAL = 2
    UNKNOWN = 3


class Track:
    """Maintains state of a track and delegates state updates to a
    state estimator."""
    def __init__(self, dt, first_msg, sensor):
        self.track_state = TrackState.UNCONFIRMED
        self.n_consecutive_measurements = 0
        self.n_consecutive_missed = 0
        self.received_measurement = False
        self.served = False
        self.sensor_id = first_msg['id']
        self.track_id = -1
        self.sensor = sensor
        # self._lane = first_msg['lane']
        # self._veh_len = first_msg['veh_len']
        # self._max_accel = first_msg['max_accel']
        # self._max_decel = first_msg['max_decel']

        self.state_estimator = KalmanFilter(sensor.get_filter(dt))

        if sensor == DSRC:
            self.type = TrackType.CONNECTED
        else:
            self.type = TrackType.UNKNOWN

    def step(self):
        """Carry out a single forward recursion of the state estimation."""
        self.state_estimator.step()

    def store(self, new_msg):
        """
        Pass a new message onto the state estimator and update state of the Track to reflect this.
        :param new_msg:
        :return:
        """
        self.state_estimator.store(new_msg)
        self.received_measurement = True
        self.n_consecutive_measurements += 1
        self.n_consecutive_missed = 0

        if not self.served and new_msg['served'] == 1:
            self.served = True

    def bsm(self):
        """Return a string containing the information needed by the optimization code
        at the most recent timestamp.

        veh_id,h,m,s,easting,northing,speed,lane,veh_len,max_accel,max_decel,served
        """
        x_hat, timestamp = self.state_estimator.state()

        if x_hat is None:
            return

        # TODO: update for handling Radar tracks

        return "{},{},{},{},{},{},{},{}".format(
            self.track_id,
            timestamp.h,
            timestamp.m,
            timestamp.s,
            x_hat[0],  # meters easting
            x_hat[2],  # meters northing
            np.round(np.sqrt(np.power(x_hat[1], 2) + np.power(x_hat[3], 2)), 3),  # m/s
            # self._lane,
            # self._veh_len,
            # self._max_accel,
            # self._max_decel,
            self.served
        )

