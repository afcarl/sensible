from __future__ import absolute_import
from __future__ import division
from sensible.sensors.DSRC import DSRC
from sensible.sensors.Radar import Radar
from .track_state import TrackState
from .track import Track
from datetime import datetime
import zmq
import time
import os

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
    def __init__(self, sensor_port, topic_filters, run_for, log_dir,
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
        self.track_confirmation_threshold = track_confirmation_threshold
        self.track_zombie_threshold = track_zombie_threshold
        self.track_drop_threshold = track_drop_threshold
        self._max_n_tracks = max_n_tracks

        # Track logger
        t = time.localtime()
        timestamp = time.strftime('%b-%d-%Y_%H%M', t)
        self._logger = open(os.path.join(log_dir, "trackLog_" + timestamp + ".csv"), 'w')
        logger_title = "TrackID,TrackState,lane,xPos,yPos,xSpeed,ySpeed\n"
        self._logger.write(logger_title)

        for t_filter in topic_filters:
            if isinstance(t_filter, bytes):
                t_filter = t_filter.decode('ascii')
            self._topic_filters.append(t_filter)
            self._subscribers[t_filter] = self._context.socket(zmq.SUB)
            self._subscribers[t_filter].connect("tcp://localhost:{}".format(sensor_port))
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
                for (topic, subscriber) in self._subscribers.items():
                    try:
                        string = subscriber.recv_string(flags=zmq.NOBLOCK)
                        m_topic, msg = string.split(" ")
                        self.associate(m_topic, pickle.loads(str(msg)))
                    except zmq.Again as e:
                        continue

            # update track state estimates, or handle no measurement
            if len(self._track_list) != 0:
                for (track_id, track) in self._track_list.items():
                    if track.received_measurement:
                        track.received_measurement = 0
                        track.step()
                    else:
                        track.n_consecutive_measurements = 0
                        track.n_consecutive_missed += 1
                        if (track.track_state == TrackState.UNCONFIRMED or
                                track.track_state == TrackState.CONFIRMED) and \
                            track.n_consecutive_missed > self.track_zombie_threshold:
                            track.track_state = TrackState.ZOMBIE
                        elif track.track_state == TrackState.ZOMBIE and \
                            track.n_consecutive_missed > self.track_drop_threshold:
                            track.track_state = TrackState.DEAD
                            self.delete_track(track_id)

            # sleep the track specialist so it runs at the given frequency
            diff = self._period - (time.time() - loop_start)
            time.sleep(diff)

    def associate(self, topic, msg):
        """
        Simple data association. For DSRC messages, vehicle IDs can be used.
        For radar zone detections, we can use global nearest neighbors.

        New tracks are created here if no existing tracks can be associated.

        :param topic: The sensor topic for this message
        :param msg: The new sensor measurement
        :return:
        """
        if topic == DSRC.topic():
            if msg['veh_id'] in self._track_list:
                track = self._track_list.get(msg['veh_id'])
                track.received_measurement = 1
                track.state_estimator.store(msg)
                track.n_consecutive_measurements += 1

                if track.track_state == TrackState.UNCONFIRMED and \
                    track.n_consecutive_measurements > self.track_confirmation_threshold:
                        track.track_state = TrackState.CONFIRMED
                elif track.track_state == TrackState.ZOMBIE:
                    track.track_state = TrackState.UNCONFIRMED
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
        """remove it from the track list."""
        del self._track_list[track_id]

    def global_nearest_neighbors(self, radar_msg):
        pass


