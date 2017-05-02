from sensible.sensors.sensible_threading import SerialThread, StoppableThread
import sensible.util.ops as ops
from sensible.tracking.vehicle_type import VehicleType
from sensible.tracking.radar_track_cfg import RadarTrackCfg
from datetime import datetime

import time
import utm

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle

import zmq

from collections import deque


class RadarSerial(SerialThread):
    def __init__(self, port, baud, local_port, radar_lat, radar_lon, mode="Tracking", lane=2, verbose=False, name="Radar"):
        super(RadarSerial, self).__init__(port, baud, name=name)
        self._verbose = verbose
        self._local_port = local_port
        self._queue = deque()
        self._lane = lane
        self.mode = mode
        self.x, self.y, self.zone, self.letter = utm.from_latlon(radar_lat, radar_lon)

        class RadarSynchronizer(StoppableThread):
            """Publish messages from a thread-safe queue"""

            def __init__(self, queue, port, topic, verbose, name="RadarSynchronizer"):
                super(RadarSynchronizer, self).__init__(name)
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
                            ops.show(' [RadarSync] Sent msg for veh: {} at second: {}'.format(queued_msg['id'],
                                                                                              queued_msg['s']),
                                     self._verbose)
                    # drop all messages
                    self._queue.clear()

            def run(self):
                while not self.stopped():
                    self.send()
                    time.sleep(1 / self._publish_freq)

        self._synchronizer = RadarSynchronizer(self._queue, self._local_port, self.topic(), self._verbose)

    @staticmethod
    def topic():
        return "Radar"

    @staticmethod
    def get_filter(dt):
        return RadarTrackCfg(dt)

    @staticmethod
    def bsm(track_id, track):
        state, t = track.state_estimator.state()

        return "{},{},{},{},{},{},{},{},{},{},{},{}".format(
            track_id,
            t.h,
            t.m,
            t.s,
            '0',  # meters easting
            state[0],  # meters northing
            abs(state[1]),  # m/s
            track.lane,
            track.veh_len,
            track.max_accel,
            track.max_decel,
            track.type
        )

    @staticmethod
    def zone_bsm(msg, track_id):

        return "{},{},{},{},{},{},{},{},{},{},{},{}".format(
            track_id,
            msg['h'],
            msg['m'],
            msg['s'],
            '0',  # meters easting
            msg['yPos'],  # meters northing
            msg['speed'],  # m/s
            msg['lane'],
            msg['veh_len'],
            msg['max_accel'],
            msg['max_decel'],
            VehicleType.CONVENTIONAL
        )

    @staticmethod
    def get_default_vehicle_type(**kwargs):
        return VehicleType.UNKNOWN

    def parse(self, msg):
        # TODO: add lane number to msg
        zone = msg['objZone']
        if self.mode == "Zone" and zone == -1:
            raise ValueError("Expected a zone number > 0")
        if self.mode == "Tracking" and zone >= 0:
            raise ValueError("Expected a zone number of -1")

        #timestamp = msg['TimeStamp']
        dt = datetime.utcnow()
        h = dt.hour
        m = dt.minute
        s = dt.second * 1000 + round(dt.microsecond / 1000)

        return {
            'id': msg['objID'],
            'h': h,
            'm': m,
            's': s,
            'xPos': self.x - msg['yPos'],
            'yPos': self.y + msg['xPos'],
            'speed': -ops.verify(-msg['ySpeed'], 6.25, 20.1),  # accept 14 mph to 45 mph ~
            'veh_len': msg['objLength'],
            'lane': self._lane,
            'max_accel': 5,
            'max_decel': -5,
            'zone': msg['objZone']
        }

    def add_to_queue(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in list(self._queue):
            if queued_msg['id'] == msg['id'] and queued_msg['s'] == msg['s']:
                # Found a duplicate
                return
        self._queue.append(msg)

    def push(self, msg):
        """Process incoming data. Overrides StoppableThread's push method."""
        self.add_to_queue(self.parse(msg))
