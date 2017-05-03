from __future__ import division

import numpy as np
import time
from datetime import datetime

import xml.etree.cElementTree as ElementTree
from collections import deque

import zmq

from sensible.sensors.sensible_threading import SensorThread, StoppableThread
from sensible.tracking.dsrc_track_cfg import DSRCTrackCfg
from sensible.tracking.vehicle_type import VehicleType

from sensible.util import ops

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class DSRC(SensorThread):
    """Thread that listens for incoming DSRC radio messages and pre-processes them.
    """

    def __init__(self, ip_address, remote_port, local_port,
                 verbose=True, msg_len=300, name="DSRC"):
        super(DSRC, self).__init__(ip_address, remote_port, msg_len, name)
        self._queue = deque()
        self._local_port = local_port
        self._blob_len = 66
        self._verbose = verbose

        class DSRCSynchronizer(StoppableThread):
            """Publish messages from a thread-safe queue"""

            def __init__(self, queue, port, topic, verbose, name="DSRCSynchronizer"):
                super(DSRCSynchronizer, self).__init__(name)
                self._publish_freq = 5  # Hz
                self._queue = queue
                self._context = zmq.Context()
                self._publisher = self._context.socket(zmq.PUB)
                # bind to tcp port _local_port
                self._publisher.bind("tcp://*:{}".format(port))
                self._topic = topic
                self._verbose = verbose

            def send(self):
                """If the queue is not empty, send the message stored at front of the queue.

                Here, the invariant is assumed to be that the queue only
                contains the unique message sent within a time frame of 0.2 seconds. The dictionary
                is pickled, so it should be un-pickled at the subscriber.

                Send 1 message from each unique DSRC_id in the queue
                """
                if len(self._queue) > 0:
                    sent_ids = []
                    for queued_msg in list(self._queue):
                        if queued_msg['id'] not in sent_ids:
                            self._publisher.send_string("{} {}".format(self._topic, pickle.dumps(queued_msg)))
                            sent_ids.append(queued_msg['id'])
                            ops.show(' [DSRCSync] Sent msg for veh: {} at second: {}'.format(queued_msg['id'],
                                                                                             queued_msg['s']),
                                     self._verbose)
                    # drop all messages
                    self._queue.clear()

            def run(self):
                while not self.stopped():
                    self.send()
                    time.sleep(1 / self._publish_freq)

        self._synchronizer = DSRCSynchronizer(self._queue, self._local_port, self.topic(), self._verbose)

    @property
    def queue(self):
        """Accessor for the synchronized queue."""
        return self._queue

    @staticmethod
    def topic():
        return "DSRC"

    @staticmethod
    def get_filter(dt):
        return DSRCTrackCfg(dt)

    @staticmethod
    def parse(msg):
        """Convert msg data from hex to decimal and filter msgs.

        Messages with the Served field set to 1 or that are unreadable
        will be dropped. We assume the messages are arriving in proper XML
        format.

        :param msg:
        :return: parsed_msg
        """
        msg = msg.split("\n", 1)[1]

        try:
            root = ElementTree.fromstring(msg)
        except ElementTree.ParseError:
            raise Exception("Unable to parse msg")

        blob1 = root.find('blob1')
        data = ''.join(blob1.text.split())

        # convert hex values to decimal
        msg_count = int(data[0:2], 16)
        veh_id = int(data[2:10], 16)
        h = ops.verify(int(data[10:12], 16), 0, 23)
        m = ops.verify(int(data[12:14], 16), 0, 59)
        s = ops.verify(int(data[14:18], 16), 0, 60000)  # ms
        lat = ops.verify(ops.twos_comp(int(data[18:26], 16), 32), -900000000, 900000000) * 1e-7
        lon = ops.verify(ops.twos_comp(int(data[26:34], 16), 32), -1799999999, 1800000000) * 1e-7
        heading = ops.verify(int(data[34:38], 16), 0, 28799) * 0.0125
	rms_lat = int(data[38:42], 16)
	rms_lon = int(data[42:46], 16)
	speed = ops.verify(int(data[46:50], 16), 0, 8190) * 0.02
        lane = int(data[50:52], 16)
        veh_len = ops.verify(int(data[52:56], 16), 0, 16383) * 0.01  # m
        max_accel = ops.verify(int(data[56:60], 16), 0, 2000) * 0.01  # m/s^2
        max_decel = ops.verify(int(data[60:64], 16), 0, 2000) * -0.01  # m/s^2
	served = int(data[64:66], 16)

        return {
            'msg_count': msg_count,
            'id': veh_id,
            'h': h,
            'm': m,
            's': s,
            'lat': lat,
            'lon': lon,
            'heading': heading,
            'speed': speed,
            'lane': lane,
            'veh_len': veh_len,
            'max_accel': max_accel,
            'max_decel': max_decel,
            'served': served
        }

    @staticmethod
    def get_default_vehicle_type(**kwargs):
        if 0 <= kwargs['id'] <= 3000000:
            return VehicleType.CONNECTED
        else:
            return VehicleType.AUTOMATED

    @staticmethod
    def bsm(track_id, track):
        state, t = track.state_estimator.state()

        return "{},{},{},{},{},{},{},{},{},{},{},{}".format(
            track_id,
            t.h,
            t.m,
            t.s,
            state[0],  # meters easting
            state[2],  # meters northing
            np.round(np.sqrt(state[1] ** 2 + state[3] ** 2), 3),  # m/s
            track.lane,
            track.veh_len,
            track.max_accel,
            track.max_decel,
            track.type
        )

    def stop(self):
        """Overrides the super class stop method, so explicitly
        call it here."""
        self._synchronizer.stop()
        super(DSRC, self).stop()

    def connect(self):
        super(DSRC, self).connect()

        # Start publishing outgoing parsed messages
        self._synchronizer.start()

    def push(self, msg):
        """Process incoming data. Overrides StoppableThread's push method."""
        self.add_to_queue(self.parse(msg))

    def add_to_queue(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in list(self._queue):
            if queued_msg['id'] == msg['id'] and queued_msg['s'] == msg['s']:
                # Found a duplicate
                return
        self._queue.append(msg)
