from __future__ import absolute_import
from __future__ import division
from sensible.sensors.DSRC import DSRC
from sensible.sensors.Radar import Radar
from .track_state import TrackState
from .track import Track
import socket
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
    def __init__(self, sensor_port, bsm_port, topic_filters, run_for, logger,
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
        # t = time.localtime()
        # timestamp = time.strftime('%b-%d-%Y_%H%M', t)
        # logger = open(os.path.join(log_dir, "trackLog_", timestamp, ".csv"), 'w')
        self._logger = logger
        logger_title = "TrackID,TrackState,timestamp,xPos,yPos,xSpeed,ySpeed\n"
        self._logger.write(logger_title)

        for t_filter in topic_filters:
            if isinstance(t_filter, bytes):
                t_filter = t_filter.decode('ascii')
            self._topic_filters.append(t_filter)
            self._subscribers[t_filter] = self._context.socket(zmq.SUB)
            self._subscribers[t_filter].connect("tcp://localhost:{}".format(sensor_port))
            self._subscribers[t_filter].setsockopt_string(zmq.SUBSCRIBE, t_filter)

        self._bsm_port = bsm_port

    @property
    def subscribers(self):
        return self._subscribers

    @subscribers.setter
    def subscribers(self, value):
        """Prevent external objects from modifying this attribute"""
        pass

    @property
    def track_list(self):
        return self._track_list

    @track_list.setter
    def track_list(self, value):
        pass

    def run(self):
        """
        Loop for a set amount of time. Each loop lasts for self._period seconds.
        A loop consists of attempts at reading self._max_n_tracks messages from each sensor.

        New sensor measurements are first associated to existing or new tracks, and then
        all tracks are updated by the new measurements. Tracks that didn't receive new measurements
        are also updated accordingly.

        """
        # Open a socket
        bsm_writer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bsm_writer.setblocking(0)
        print("  [*] Opened UDP socket connection to send BSMs to port {}".format(self._bsm_port))

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
                    if track.received_measurement == 1:
                        track.received_measurement = 0
                        track.step()
                    else:
                        track.n_consecutive_measurements = 0
                        track.n_consecutive_missed += 1
                        if (track.track_state == TrackState.UNCONFIRMED or
                                track.track_state == TrackState.CONFIRMED) and \
                            track.n_consecutive_missed >= self.track_zombie_threshold:
                            track.track_state = TrackState.ZOMBIE
                        elif track.track_state == TrackState.ZOMBIE and \
                            track.n_consecutive_missed >= self.track_drop_threshold:
                            track.track_state = TrackState.DEAD
                            self.delete_track(track_id)

            # Send measurements from confirmed tracks to the optimization
            self.send_bsms(bsm_writer)

            # sleep the track specialist so it runs at the given frequency
            diff = self._period - (time.time() - loop_start)
            time.sleep(diff)

        bsm_writer.close()
        print("  [*] Closed UDP port {}".format(self._bsm_port))

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
                track.n_consecutive_missed = 0

                if track.track_state == TrackState.UNCONFIRMED and \
                    track.n_consecutive_measurements >= self.track_confirmation_threshold:
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
        self._track_list[msg['veh_id']] = Track(self._period, msg)
        self._track_list[msg['veh_id']].store(msg)

    def delete_track(self, track_id):
        """remove it from the track list."""
        print("  [*] Dropping track {}".format(track_id))
        del self._track_list[track_id]

    def global_nearest_neighbors(self, radar_msg):
        """
        For each active track, check whether
        :param radar_msg:
        :return:
        """
        pass

    def send_bsms(self, my_sock):
        """
        Collect the latest filtered measurements from each confirmed track,
        and if the tracked object has not yet been served, send a BSM
        :return:
        """
        for (track_id, track) in self._track_list.items():
            if track.track_state == TrackState.CONFIRMED and not track.served:
                try:
                    state, t_stamp = track.state_estimator.predicted_state()
                    #print(track.state_estimator.predicted_state())
                    self._logger.write("{},{},{},{},{},{},{}".format(
                        track_id, TrackState.to_string(track.track_state),
                        t_stamp.to_string(),state[0],state[1], state[2], state[3]
                    ))
                    print("{},{},{},{},{},{},{}".format(
                        track_id, TrackState.to_string(track.track_state),
                        t_stamp.to_string(),state[0],state[1], state[2], state[3]
                    ))
                    #my_sock.sendto(track.bsm(), ("localhost", self._bsm_port))
                except socket.error as e:
                    # log the error
                    print("  [*] Couldn't send BSM for confirmed track ["
                          + track_id + "] due to error: " + e.message)



