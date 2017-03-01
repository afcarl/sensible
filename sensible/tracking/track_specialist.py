from __future__ import absolute_import
from __future__ import division
from sensible.sensors.DSRC import DSRC
from sensible.sensors.Radar import Radar
from .track_state import TrackState
from .track import Track
from datetime import datetime
import zmq
import time

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class TrackSpecialist:
    """
    Manages the ZeroMQ subscribers to all sensor topics, as well as oversees
    publishing BSMs to the optimization algorithm.

    Responsible for updating track states and carrying out data association
    for new measurements.

    """
    def __init__(self, sensor_network_port, topic_filters, run_for, log_file,
                 frequency=5,
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
        self._log = log_file

        for t_filter in topic_filters:
            if isinstance(t_filter, bytes):
                t_filter = t_filter.decode('ascii')
            self._topic_filters.append(t_filter)
            self._subscribers[t_filter] = self._context.socket(zmq.SUB)
            self._subscribers[t_filter].connect("tcp://localhost:{}".format(sensor_network_port))
            self._subscribers[t_filter].setsockopt_string(zmq.SUBSCRIBE, t_filter)

    @property
    def subscribers(self):
        return self._subscribers

    @property
    def track_list(self):
        return self._track_list

    def run(self):
        """
        Loop for a set amount of time. Each loop lasts for self._period seconds.
        A loop consists of attempts at reading self._max_n_tracks messages from each sensor.

        New sensor measurements are first associated to existing or new tracks, and then
        all tracks are updated by the new measurements. Tracks that didn't receive new measurements
        are also updated accordingly.

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
        Simple data association. For DSRC messages, vehicle IDs can be used.
        For radar zone detections, we can use global nearest neighbors.

        :param topic: The sensor topic for this message
        :param msg: The new sensor measurement
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
        """A new UNCONFIRMED track is created, and this message is associated
        with it."""
        self._track_list[msg['veh_id']] = Track()
        self._track_list[msg['veh_id']].store(msg)

    def delete_track(self, track_id):
        """Dump the track history to the log file and remove it from the track list."""
        self._log.write('[track drop] track id: {} | utctime: {}\n', track_id, datetime.utcnow())
        self._track_list[track_id].state_estimator.dump(self._log)
        self._track_list[track_id] = None

    def global_nearest_neighbors(self, radar_msg):
        pass


