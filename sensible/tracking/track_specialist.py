from __future__ import absolute_import
from sensible.sensors.DSRC import DSRC
from .track_state import TrackState
import zmq
import time


try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class TrackSpecialist:
    """
    Manages all tracks and network connections
    """
    def __init__(self, sensor_network_port, topic_filters, run_for, track_confirmation_threshold=3,
                 track_zombie_threshold=3, track_drop_threshold=7):
        self._context = zmq.Context()
        self._subscriber = self._context.socket(zmq.SUB)
        self._subscriber.connect("tcp://localhost:{}".format(sensor_network_port))

        for filter in topic_filters:
            if isinstance(filter, bytes):
                filter = filter.decode('ascii')
            self._subscriber.setsockopt_string(zmq.SUBSCRIBE, filter)

        self._track_map = {}
        self._run_for = run_for
        self._track_confirmation_threshold = track_confirmation_threshold
        self._track_zombie_threshold = track_zombie_threshold
        self._track_drop_threshold = track_drop_threshold

    def run(self):
        t_end = time.time() + self._run_for

        while time.time() < t_end:
            try:
                string = self._subscriber.recv_string(flags=zmq.NOBLOCK)
                topic, msg = string.split(" ")
                self.new_measurement(topic, pickle.loads(str(msg)))
            except zmq.Again as e:
                continue

    def new_measurement(self, topic, msg):
        if topic == DSRC.topic():
            id = msg['veh_id']
            for track in self._track_map:
                if track.id == id:
                    if track.state == TrackState.CONFIRMED:
                        track.step(msg)
                    elif track.state == TrackState.UNCONFIRMED:
                        if track.n_consecutive_msgs >= self._track_confirmation_threshold:
                            track.state = TrackState.CONFIRMED
                            track.step(msg)
                        else:
                            track.n_consecutive_msgs += 1
                            track.z.append(msg)

    def create_track(self):

    def delete_track(self, track_id):

    def global_nearest_neighbors(self):


