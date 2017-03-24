from __future__ import absolute_import
from __future__ import division

import socket
import zmq
import time

from sensible.sensors.DSRC import DSRC
from sensible.sensors.radar import Radar
from sensible.util import ops
from .state_estimator import StateEstimator
from .state_estimator import TimeStamp

from .track_state import TrackState
from .track import Track

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


def dump(content, filename):
    """
    pickle content to filename
    """
    try:
        with open(filename, 'wb') as outfile:
            pickle.dump(content, outfile)
            outfile.close()
    except IOError as e:
        print("Fail: error to open file: {}".format(filename))


class TrackSpecialist:
    """
    Manages the ZeroMQ subscribers to all sensor topics, as well as oversees
    publishing BSMs to the optimization algorithm.

    Responsible for updating track states and carrying out data association
    for new measurements.

    """

    def __init__(self, sensors, bsm_port, run_for, logger,
                 frequency=5,
                 track_confirmation_threshold=5,
                 track_zombie_threshold=3,
                 track_drop_threshold=5,
                 max_n_tracks=5):
        self._context = zmq.Context()
        self._subscribers = {}
        self._topic_filters = []
        self._track_list = {}
        self._period = 1 / frequency  # seconds
        self._run_for = run_for
        self._max_n_tracks = max_n_tracks

        self.track_confirmation_threshold = track_confirmation_threshold
        self.track_zombie_threshold = track_zombie_threshold
        self.track_drop_threshold = track_drop_threshold

        self._logger = logger
        logger_title = "TrackID,TrackState,Filtered,timestamp,xPos,yPos,xSpeed,ySpeed\n"
        self._logger.write(logger_title)

        topic_filters = sensors['topic_filters']
        sensor_ports = sensors['sensor_ports']

        for pair in list(zip(topic_filters, sensor_ports)):
            topic_filter = pair[0]
            port = pair[1]
            if isinstance(topic_filter, bytes):
                topic_filter = topic_filter.decode('ascii')
            self._topic_filters.append(topic_filter)
            self._subscribers[topic_filter] = self._context.socket(zmq.SUB)
            self._subscribers[topic_filter].connect("tcp://localhost:{}".format(port))
            self._subscribers[topic_filter].setsockopt_string(zmq.SUBSCRIBE, topic_filter)

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
                    if track.received_measurement:
                        track.step()
                        track.received_measurement = False
                    else:
                        track.n_consecutive_measurements = 0
                        track.n_consecutive_missed += 1

                        if track.track_state == TrackState.ZOMBIE and \
                                        track.n_consecutive_missed >= self.track_drop_threshold:
                            track.track_state = TrackState.DEAD
                            self.delete_track(track_id)
                        else:
                            track.state_estimator.store(None)
                            # do a step without receiving a new measurement
                            # by propagating the predicted state
                            track.step()

                            if (track.track_state == TrackState.UNCONFIRMED or
                                        track.track_state == TrackState.CONFIRMED) and \
                                            track.n_consecutive_missed >= self.track_zombie_threshold:
                                track.track_state = TrackState.ZOMBIE

            # sleep the track specialist so it runs at the given frequency
            diff = self._period - (time.time() - loop_start)
            if diff > 0:
                time.sleep(diff)

            # Send measurements from confirmed tracks to the optimization
            self.send_bsms(bsm_writer)

        bsm_writer.close()
        # self._logger.close()
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
                # Occasionally, the synchronizer may allow 2 messages
                # to arrive at 1 cycle. Only accept one by enforcing
                # the invariant "each track receives <= 1 message per cycle"
                if not track.received_measurement:
                    track.received_measurement = True
                    track.n_consecutive_measurements += 1
                    track.n_consecutive_missed = 0

                    track.state_estimator.store(msg)

                    if track.track_state == TrackState.UNCONFIRMED and \
                                    track.n_consecutive_measurements >= \
                                    self.track_confirmation_threshold:
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
        For each active track, check whether the radar measurement
        falls near the track based on the Mahalanobis distance.

        Using Chi-squared tables for 4 degrees of freedom (one for each
        dimension of the state vector), for different p-values

        p = 0.05 -> 9.49
        p = 0.01 -> 13.28
        p = 0.001 -> 18.47

        :param radar_msg:
        :return:
        """
        radar_measurement = StateEstimator.parse_msg(radar_msg)
        # t = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
        #
        # gnn_dict = {'time': t.to_fname_string(), 'radar': radar_measurement}
        # dump(gnn_dict,
        #      "C:\\Users\\pemami\\Workspace\\Github\\sensible\\tests\\data\\trajectories\\radar-" + t.to_fname_string() + ".pkl")

        results = []
        for (track_id, track) in self._track_list.items():

            kf_state, t_stamp = track.state_estimator.predicted_state()
            cov = track.state_estimator.predicted_state_covariance()
            md = ops.mahalanobis(radar_measurement, kf_state, cov)

            print("  [GNN] Vehicle {} has a Mahalanobis distance of {} "
                  "to the detection".format(track_id, md))

            if md <= 400:
                results.append((track_id, md))

            kf_log_str = "  [GNN] Kalman Filter: {},{},{},{},{},{},{}\n".format(
                track_id, TrackState.to_string(track.track_state),
                t_stamp, kf_state[0], kf_state[2],
                kf_state[1], kf_state[3]
            )
            print(kf_log_str)

        if len(results) == 0:
            # radar measurement didn't fall near any tracked vehicles, so tentatively
            # associate as a conventional vehicle
            print("  [GNN] Conventional vehicle detected, sending BSM...")
        else:
            if len(results) > 1:
                print("  [Warning] {} vehicles within gating region of radar detection!".format(len(results)))
                # choose the closest
                sorted_results = sorted(results, key=lambda pair: len(pair[1]))
                id = sorted_results[0][0]
                print("  [GNN] Associating radar detection with vehicle {}".format(id))
            else:
                r = results[0]
                print("  [GNN] Associating radar detection with vehicle {}".format(r[1]))
                # track = self._track_list[r[0]]
                # potentially fuse this with the kalman filter

                radar_t_stamp = TimeStamp(radar_msg['h'], radar_msg['m'], radar_msg['s'])
                radar_log_str = " [GNN] Radar msg: {},{},{},{},{}\n".format(
                    radar_t_stamp.to_string(), radar_measurement[0], radar_measurement[2],
                    radar_measurement[1], radar_measurement[3]
                )
                print(radar_log_str)

    def send_conventional_veh_bsm(self, radar_msg):
        """

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
            if track.track_state == TrackState.CONFIRMED or \
                                    track.track_state == TrackState.ZOMBIE and not track.served:

                kf_state, t_stamp = track.state_estimator.predicted_state()
                ###########
                # For Debug
                ###########
                # cov = track.state_estimator.predicted_state_covariance()
                # dump({'time': t_stamp, 'kf': kf_state, 'cov': cov},
                #      "C:\\Users\\pemami\\Workspace\\Github\\sensible\\tests\\data\\trajectories\\kf-" + t_stamp + ".pkl")

                kf_log_str = "{},{},{},{},{},{},{},{}\n".format(
                    track_id, TrackState.to_string(track.track_state), 1,
                    t_stamp, kf_state[0], kf_state[2],
                    kf_state[1], kf_state[3]
                )
                self._logger.write(kf_log_str)
                print(kf_log_str)

                m, _ = track.state_estimator.get_latest_measurement()

                if m is not None:
                    m_log_str = "{},{},{},{},{},{},{},{}\n".format(
                        track_id, TrackState.to_string(track.track_state), 0,
                        t_stamp, m[0], m[2], m[1], m[3]
                    )
                    self._logger.write(m_log_str)


                    # if track.track_state == TrackState.CONFIRMED:
                    #     try:
                    #         # my_sock.sendto(track.bsm(), ("localhost", self._bsm_port))
                    #     except socket.error as e:
                    #         # log the error
                    #         print("  [*] Couldn't send BSM for confirmed track ["
                    #               + track_id + "] due to error: " + e.message)
