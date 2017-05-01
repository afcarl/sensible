import numpy as np

from sensible.tracking.track_state import TrackState
from sensible.tracking.kalman_filter import KalmanFilter
from sensible.sensors.DSRC import DSRC
from sensible.sensors.radar import Radar
import sensible.util.time_stamp as ts


class TrackType:
    AUTOMATED = 0
    CONNECTED = 1
    CONVENTIONAL = 2
    UNKNOWN = 3


class Track(object):
    """Maintains state of a track and delegates state updates to a
    state estimator."""
    def __init__(self, dt, first_msg, sensor):
        self.n_consecutive_measurements = 0
        self.n_consecutive_missed = 0
        self.received_measurement = False
        self.served = False
        self._fused = False
        self.fused_track_id = None  # the track id of the
        self._veh_id = first_msg['id']
        # self._lane = first_msg['lane']
        # self._veh_len = first_msg['veh_len']
        # self._max_accel = first_msg['max_accel']
        # self._max_decel = first_msg['max_decel']

        # TODO: set connected or automated based on ID
        self.track_state = TrackState.UNCONFIRMED
        self.sensor = sensor

        self.state_estimator = KalmanFilter(sensor.get_filter(dt))

        if sensor == DSRC:
            self.update_type(self._veh_id)
        else:
            self._type = TrackType.UNKNOWN

    @property
    def fused(self):
        return self._fused

    @fused.setter
    def fused(self, val):
        if val:
            assert self.sensor == DSRC
        self._fused = val

    def update_type(self, veh_id):
        """Useful for radar tracks that are associated with DSRC tracks."""
        if 0 <= veh_id <= 3000000:
            self._type = TrackType.CONNECTED
        else:
            self._type = TrackType.AUTOMATED

    def step(self):
        """Carry out a single forward recursion of the state estimation."""
        self.state_estimator.step()

    def fuse_estimates(self, track):
        """Fuse this track estimates with the current estimates from argument track."""
        if self._fused:
            self.state_estimator.covariance_intersection(track.state(), track.process_covariance())

    def store(self, new_msg):
        """
        Pass a new message onto the state estimator and update state of the Track to reflect this.
        :param new_msg:
        :return:
        """
        self.state_estimator.store(new_msg, ts.TimeStamp(new_msg['h'], new_msg['m'], new_msg['s']))
        self.received_measurement = True
        self.n_consecutive_measurements += 1
        self.n_consecutive_missed = 0

        if not self.served and self.sensor == DSRC and new_msg['served'] == 1:
            self.served = True

    def bsm(self, track_id):
        """Return a string containing the information needed by the optimization code
        at the most recent timestamp.

        veh_id,h,m,s,easting,northing,speed,lane,veh_len,max_accel,max_decel,served
        """
        x_hat, timestamp = self.state_estimator.state()

        if x_hat is None:
            return

        # TODO: update for handling Radar tracks

        return "{},{},{},{},{},{},{},{}".format(
            track_id,
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

