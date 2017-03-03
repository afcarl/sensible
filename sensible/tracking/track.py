from __future__ import absolute_import
from .track_state import TrackState
from .kalman_filter import KalmanFilter


class Track:
    """Keeps track of the state of a track, both
    lifecycle and state estimation."""
    def __init__(self):
        self._track_state = TrackState.UNCONFIRMED
        self.n_consecutive_measurements = 0
        self.n_consecutive_missed = 0
        self.state_estimator = KalmanFilter()
        self.received_measurement = 0
        self._served = 0

    @property
    def served(self):
        return self._served

    @property
    def track_state(self):
        return self._track_state

    def step(self):
        self.state_estimator.step()

    def store(self, new_msg):
        self.state_estimator.store(new_msg)
        self.received_measurement = 1
        self.n_consecutive_measurements += 1
        self.n_consecutive_missed = 0

        if not self._served and new_msg['served'] == 1:
            self._served = 1

    def bsm(self):
        """Return a string containing the information needed by the optimization code."""
        # return "{},{},{},{},{}".format()
        pass
