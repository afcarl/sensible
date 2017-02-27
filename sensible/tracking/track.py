from __future__ import absolute_import
from .track_state import TrackState


class Track:

    def __init__(self, state_estimator):
        self._track_state = TrackState.UNCONFIRMED
        self.n_consecutive_measurements = 0
        self.n_consecutive_missed = 0
        self.state_estimator = state_estimator
        self.received_measurement = 0

    @property
    def track_state(self):
        return self._track_state

    def step(self, new_measurement):
        self.state_estimator.step(new_measurement)
