from __future__ import absolute_import
from __future__ import division
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
    def __init__(self, sensor_network_port, topic_filters, run_for, frequency,
                 track_confirmation_threshold=5,
                 track_zombie_threshold=5,
                 track_drop_threshold=8,
                 max_n_tracks=5):
        self._context = zmq.Context()
        self._subscribers = {}
        self._topic_filters = []
        self._track_list = {}
        self._period = 1 / frequency  # seconds
        self._run_for = run_for
        self._track_confirmation_threshold = track_confirmation_threshold
        self._track_zombie_threshold = track_zombie_threshold
        self._track_drop_threshold = track_drop_threshold
        self._max_n_tracks = max_n_tracks

        for t_filter in topic_filters:
            if isinstance(t_filter, bytes):
                t_filter = t_filter.decode('ascii')
            self._topic_filters.append(t_filter)
            self._subscribers[t_filter] = self._context.socket(zmq.SUB)
            self._subscribers[t_filter].connect("tcp://localhost:{}".format(sensor_network_port))
            self._subscribers[t_filter].setsockopt_string(zmq.SUBSCRIBE, t_filter)

    def run(self):
        """

        :return:
        """
        t_end = time.time() + self._run_for

        while time.time() < t_end:
            loop_start = time.time()

            for i in range(self._max_n_tracks):
                for subscriber in self._subscribers:
                    try:
                        string = subscriber.recv_string(flags=zmq.NOBLOCK)
                        topic, msg = string.split(" ")
                        self.associate(topic, pickle.loads(str(msg)))
                    except zmq.Again as e:
                        continue

            # update track state estimates, or handle no measurement
            for track in self._track_list:
                if track.received_msg:
                    track.received_msg = 0
                    track.step()
                else:
                    track.n_consecutive_measurements = 0
                    track.n_consecutive_missed += 1
                    if (track.state == TrackState.UNCONFIRMED or
                            track.state == TrackState.CONFIRMED) and \
                        track.n_consecutive_missed > self._track_zombie_threshold:
                        track.state = TrackState.ZOMBIE
                    elif track.state == TrackState.ZOMBIE and \
                        track.n_consecutive_missed > self._track_drop_threshold:
                        track.state = TrackState.DEAD
                        self.delete_track(track)

            # sleep the track specialist so it runs at the given frequency
            diff = self._period - (time.time() - loop_start)
            time.sleep(diff)

    def associate(self, topic, msg):
        """

        :param topic:
        :param msg:
        :return:
        """
        if topic == DSRC.topic():
            if self._track_list.has_key(msg['veh_id']):
                track = self._track_list.get(msg['veh_id'])
                track.received_msg = 1
                track.state_estimator.store(msg)
                track.n_consecutive_msgs += 1

                if track.state == TrackState.UNCONFIRMED and \
                    track.n_consecutive_msgs > self._track_confirmation_threshold:
                        track.state = TrackState.CONFIRMED
                elif track.state == TrackState.ZOMBIE:
                    track.state = TrackState.UNCONFIRMED
            else:
                # create new unconfirmed track
                self.create_track(msg)
        elif topic == Radar.topic():
            self.global_nearest_neighbors(msg)

    def create_track(self, msg):

    def delete_track(self, track):

    def global_nearest_neighbors(self, radar_msg):


