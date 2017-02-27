from __future__ import absolute_import
from .track_state import TrackState


class Track:

    def __init__(self):
        self._track_state = TrackState.UNCONFIRMED
        self.n_consecutive_msgs = 0
        self.z = []  # measurements

    @property
    def track_state(self):
        return self._track_state

    def step(self, new_measurement):
        self.z.append(new_measurement)
