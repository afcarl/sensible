from __future__ import division

import socket
import time

import zmq

import sensible.tracking.data_associator as data_associator
import sensible.tracking.track_fusion as tf
from sensible.sensors.DSRC import DSRC
from sensible.sensors.radar import Radar
from sensible.tracking.track import Track
from sensible.tracking.track_state import TrackState
from sensible.tracking.vehicle_type import VehicleType
from sensible.util import ops

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

    We assume that each sensor sending track information to the TrackSpecialist
    provides a track id that does not clash with any other currently active tracks
    from any sensor. This is a precondition that can be maintained by having sensors
    produce IDs in non-overlapping ranges.
    """

    def __init__(self, sensors, bsm_port, run_for, track_logger, n_scan,
                 association=data_associator.single_hypothesis_track_association,
                 association_threshold=35,
                 verbose=False,
                 frequency=5,
                 motion_model='CV',
                 track_confirmation_threshold=5,
                 track_zombie_threshold=5,
                 track_drop_threshold=10,
                 max_n_tracks=15):
        self._context = zmq.Context()
        self._subscribers = {}
        self._topic_filters = []
        self._track_list = {}
        self._sensor_id_map = {}  # maps individual sensor ids to track ids
        self._sensor_id_idx = 0
        self._period = 1 / frequency  # seconds
        self._run_for = run_for
        self._max_n_tracks = max_n_tracks
        self._n_scan = n_scan
        self._verbose = verbose
        self._logger = track_logger
        self._association_threshold = association_threshold
        self._motion_model = motion_model

        self.track_confirmation_threshold = track_confirmation_threshold
        self.track_zombie_threshold = track_zombie_threshold
        self.track_drop_threshold = track_drop_threshold

        self.track_association = association

        topic_filters = sensors['topic_filters']
        sensor_ports = sensors['sensor_ports']

        for pair in list(zip(topic_filters, sensor_ports)):
            topic_filter = pair[0]
            port = pair[1]
            if isinstance(topic_filter, bytes):
                topic_filter = topic_filter.decode('ascii')
            self._topic_filters.append(topic_filter)
            self._subscribers[topic_filter] = self._context.socket(zmq.SUB)
            self._subscribers[topic_filter].connect(
                "tcp://localhost:{}".format(port))
            self._subscribers[topic_filter].setsockopt_string(
                zmq.SUBSCRIBE, topic_filter)

        self._bsm_port = bsm_port

        # Open a socket for sending tracks
        self._bsm_writer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._bsm_writer.setblocking(0)
        ops.show("  [*] Opened UDP socket connection to send BSMs to port {}\n".format(
            self._bsm_port), self._verbose)

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

    @property
    def sensor_id_map(self):
        return self._sensor_id_map

    @track_list.setter
    def track_list(self, value):
        pass

    @sensor_id_map.setter
    def sensor_id_map(self, value):
        pass

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

            message_queue = []

            # since there could be many vehicles being tracked via DSRC/Radar/etc,
            # we need to attempt to read messages 2*max_n_tracks times
            # to get them all. This is because there could be N AVs, which
            # are tracked both by radar and DSRC, so we want to be
            # able to read all of them
            for i in range(2 * self._max_n_tracks):
                for (topic, subscriber) in self._subscribers.items():
                    try:
                        string = subscriber.recv_string(flags=zmq.NOBLOCK)
                        m_topic, msg = string.split(" ", 1)
                        message_queue.append((m_topic, pickle.loads(str(msg))))
                    except zmq.Again as e:
                        continue

            for msg in message_queue:
                self.measurement_association(msg[0], msg[1])

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
                            # if the track is a fused track, tell the other
                            # track to stop fusing estimates with it
                            if len(track.fused_track_ids) > 0:
                                for fused_track_id in track.fused_track_ids:
                                    # check if the track already got deleted
                                    # during this iteration
                                    if fused_track_id in self._track_list:
                                        # remove the track being deleted from
                                        # the other track's fusion list
                                        self._track_list[fused_track_id].fused_track_ids.remove(track_id)
                                        # if the other track is no longer fusing estimates with any other track,
                                        # reset it's fusion state
                                        if len(self._track_list[fused_track_id].fused_track_ids) == 0:
                                            self._track_list[
                                                fused_track_id].state_estimator.fused_track = False
                            self.delete_track(track_id)

                        else:
                            # generate a new time stamp anyways
                            prev_ts = track.state_estimator.t[-1]
                            prev_ts.s = str(float(prev_ts.s) +
                                            track.state_estimator.sensor_cfg.dt * 1000)
                            track.state_estimator.store(msg=None, time=prev_ts)
                            # do a step without receiving a new measurement
                            # by propagating the predicted state
                            track.step()

                            if (track.track_state == TrackState.UNCONFIRMED or
                                    track.track_state == TrackState.CONFIRMED) and \
                                    track.n_consecutive_missed >= self.track_zombie_threshold:
                                track.track_state = TrackState.ZOMBIE

                # fuse estimates
                for (track_id, track) in self._track_list.items():
                    if track.state_estimator.fused_track and track.fusion_method is not None:
                        # collect all tracks being fused with this track
                        fused_tracks = []
                        for (other_track_id, other_track) in self._track_list.items():
                            if track_id == other_track_id:
                                continue
                            else:
                                if other_track_id in track.fused_track_ids:
                                    fused_tracks.append(other_track)
                        if len(fused_tracks) > 0:
                            track.fuse_estimates(fused_tracks)
                    elif len(track.state_estimator.x_k) == len(track.state_estimator.x_k_fused) - 1:
                        track.fuse_empty()

            # sleep the track specialist so it runs at the given frequency
            diff = self._period - (time.time() - loop_start)
            if diff > 0:
                time.sleep(diff)

            # Send measurements from confirmed tracks to the optimization
            self.send_bsms()

        self._bsm_writer.close()
        ops.show(
            "  [*] Closed UDP port {}\n".format(self._bsm_port), self._verbose)

    def measurement_association(self, topic, msg):
        """
        Track-to-track and measurement-to-track association.
        For DSRC messages, vehicle IDs can be used.
        For radar tracks and zone detections, we use global nearest neighbors.

        New tracks are created here if no existing tracks can be associated.

        :param topic: The sensor topic for this message
        :param msg: The new sensor measurement
        :return:
        """
        if topic == Radar.topic() and msg['objZone'] > -1:
            # measurement-to-track association
            result, match_id = self.track_association(self.track_list, msg,
                                                      threshold=self._association_threshold,
                                                      method="measurement-to-track", verbose=self._verbose)
            if result == 0x5:
                # send BSM for new conventional vehicle.
                try:
                    self._bsm_writer.sendto(Radar.zone_bsm(
                        msg, self._sensor_id_idx), ("localhost", self._bsm_port))
                    self._sensor_id_idx += 1
                except socket.error as e:
                    # log the error
                    ops.show("  [!] Couldn't send BSM for detected conventional vehicle "
                             "[{}] due to error: {}\n".format(match_id, e.message), self._verbose)
            elif result == 0x6:
                # match_id is that of the corresponding DSRC track. Add code
                # for updating GUI
                pass
        else:
            if msg['id'] in self._sensor_id_map:
                track_id = self._sensor_id_map[msg['id']]
                track = self._track_list.get(track_id)
                # Occasionally, the synchronizer may allow 2 messages
                # to arrive at 1 cycle. Only accept one by enforcing
                # the invariant "each track receives <= 1 message per cycle"
                if not track.received_measurement:

                    track.store(msg, self._track_list)

                    if track.track_state == TrackState.UNCONFIRMED and \
                            track.n_consecutive_measurements >= \
                            self.track_confirmation_threshold:
                        track.track_state = TrackState.CONFIRMED

                        # attempt to fuse tracks
                        result, match_id = self.track_association(
                            self.track_list, (track_id, track), threshold=self._association_threshold,
                            verbose=self._verbose)

                        if result == 0x1:
                            track.type = VehicleType.CONVENTIONAL
                        elif result == 0x2:
                            self.merge_tracks(
                                dsrc_track_id=match_id, radar_track_id=track_id)
                        elif result == 0x3:
                            pass  # nothing to do for this case
                        elif result == 0x4:
                            self.merge_tracks(
                                dsrc_track_id=track_id, radar_track_id=match_id)

                    elif track.track_state == TrackState.ZOMBIE:
                        track.track_state = TrackState.UNCONFIRMED
            else:
                # create new unconfirmed track
                self.create_track(msg, topic)

    def create_track(self, msg, topic):
        """
        A new UNCONFIRMED track is created and msg is associated with it.

        :param msg:
        :param topic:
        :return:
        """
        fusion_method = None
        sensor = None

        if topic == DSRC.topic():
            sensor = DSRC
            fusion_method = tf.covariance_intersection
        elif topic == Radar.topic():
            sensor = Radar

        self._sensor_id_map[msg['id']] = self._sensor_id_idx
        self._sensor_id_idx += 1
        self._track_list[self._sensor_id_map[msg['id']]] = Track(
            self._period, msg, sensor, self._motion_model, self._n_scan, fusion_method)
        self._track_list[self._sensor_id_map[
            msg['id']]].store(msg, self._track_list)
        ops.show(
            "  [*] Creating track {} for {} track with ID {}\n".format(self._sensor_id_map[msg['id']],
                                                                     topic, msg['id']), self._verbose)

    def delete_track(self, track_id):
        """remove it from the track list."""
        ops.show("  [*] Dropping track {}\n".format(track_id), self._verbose)
        self.log_track(track_id, self._track_list[track_id])

        msg_id = None
        for k, v in self._sensor_id_map.items():
            if v == track_id:
                msg_id = k
        if msg_id is None:  # track_id has already been removed
            return
        del self._sensor_id_map[msg_id]
        del self._track_list[track_id]

    def merge_tracks(self, dsrc_track_id, radar_track_id):
        """
        :param dsrc_track_id:
        :param radar_track_id:
        :return:
        """
        ops.show("  [*] Fusing DSRC track {} and radar track {}\n".format(
            dsrc_track_id, radar_track_id), self._verbose)
        self._track_list[dsrc_track_id].state_estimator.fused_track = True
        self._track_list[dsrc_track_id].fused_track_ids.append(radar_track_id)
        # set the type of the radar track to be connected or automated
        self._track_list[radar_track_id].type = DSRC.get_default_vehicle_type(
            id=dsrc_track_id)
        self._track_list[radar_track_id].fused_track_ids.append(dsrc_track_id)

    def send_bsms(self):
        """
        Collect the latest filtered measurements from each confirmed track,
        and if the tracked object has not yet been served, send a BSM
        :return:
        """

        for (track_id, track) in self._track_list.items():
            if track.track_state == TrackState.UNCONFIRMED or \
                            track.track_state == TrackState.CONFIRMED or track.track_state == TrackState.ZOMBIE:

                self.log_track(track_id, track)

                if track.track_state == TrackState.CONFIRMED and not track.served:
                    # only need to send 1 BSM per fused tracks
                    if not track.state_estimator.fused_track and len(track.fused_track_ids) > 0:
                        continue
                    else:
                        try:
                            self._bsm_writer.sendto(track.sensor.bsm(
                                track_id, track), ("localhost", self._bsm_port))
                        except socket.error as e:
                            # log the error
                            ops.show("  [*] Couldn't send BSM for track [{}]"
                                     " due to error: {}\n".format(track_id,  e.message), self._verbose)

    def log_track(self, track_id, track):
        if self._logger is not None and len(track.state_estimator.x_k) > 2:
            kf_str, msg_str = track.state_estimator.to_string()

            if track.state_estimator.fused_track:
                kf_unfused_str, msg_str = track.state_estimator.to_string(get_unfused=True)

            if track.state_estimator.fused_track:
                label = '2'
            else:
                label = '1'

            if track.sensor == Radar:
                sens = "Radar"
            elif track.sensor == DSRC:
                sens = "DSRC"

            if track.served:
                served = "1"
            else:
                served = "0"

            self._logger.write(str(track_id) + ',' + TrackState.to_string(track.track_state) +
                               ',' + label + ',' + kf_str[:-1] + ',' + sens + ',' + served + '\n')
            if track.state_estimator.fused_track:
                self._logger.write(str(track_id) + ',' + TrackState.to_string(track.track_state) +
                                   ',' + '1' + ',' + kf_unfused_str[:-1] + ',' + sens + ',' + served + '\n')
            self._logger.write(str(track_id) + ',' + TrackState.to_string(track.track_state) +
                               ',' + str(0) + ',' + msg_str[:-1] + ',' + sens + ',' + served + '\n')
