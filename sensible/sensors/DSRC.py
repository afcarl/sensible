from __future__ import absolute_import
from __future__ import division

import xml.etree.cElementTree as ElementTree
from collections import deque

import zmq
import time

from sensible.util.sensible_threading import SensorThread, StoppableThread
from ..util import ops
from ..util.exceptions import ParseError

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class DSRC(SensorThread):
    """Thread that listens for incoming DSRC radio messages and pre-processes them.

    """

    def __init__(self, ip_address, remote_port, local_port, msg_len=277, name="DSRC"):
        super(DSRC, self).__init__(name, msg_len)
        self._queue = deque()
        self._ip_address = ip_address
        self._port = remote_port
        self._local_port = local_port
        self._blob_len = 58

        class DSRCSynchronizer(StoppableThread):
            """Publish messages from a thread-safe queue"""

            def __init__(self, queue, port, topic, name="DSRCSynchronizer"):
                super(DSRCSynchronizer, self).__init__(name)
                self._publish_freq = 5  # Hz
                self._queue = queue
                self._context = zmq.Context()
                self._publisher = self._context.socket(zmq.PUB)
                # bind to tcp port _local_port
                self._publisher.bind("tcp://*:{}".format(port))
                self._topic = topic

            def send(self):
                """If the queue is not empty, send the message stored at front of the queue.

                Here, the invariant is assumed to be that the queue only
                contains the unique message sent within a time frame of 0.2 seconds. The dictionary
                is pickled, so it should be un-pickled at the subscriber.
                """
                if len(self._queue) > 0:
                    self._publisher.send_string("{} {}".format(self._topic, pickle.dumps(self._queue.pop())))

            def run(self):
                while not self.stopped():
                    self.send()
                    time.sleep(1 / self._publish_freq)

        self._synchronizer = DSRCSynchronizer(self._queue, self._local_port, self.topic())

    @property
    def queue(self):
        """Accessor for the synchronized queue."""
        return self._queue

    @staticmethod
    def topic():
        return "DSRC"

    def stop(self):
        self._synchronizer.stop()
        super(DSRC, self).stop()

    def connect(self):
        # open connection to incoming DSRC messages
        self._sock.bind((self._ip_address, self._port))
        self._sock.setblocking(0)

        # Start publishing outgoing parsed messages
        self._synchronizer.start()

    def push(self, msg):
        """Process incoming data. Overrides StoppableThread's push method."""
        self.add_to_queue(self.parse(msg))

    def add_to_queue(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in self._queue:
            if msg['s'] == queued_msg['s']:
                # Found a duplicate
                return
        self._queue.append(msg)

    def parse(self, msg):
        """Convert msg data from hex to decimal and filter msgs.

        Messages with the Served field set to 1 or that are unreadable
        will be dropped. We assume the messages are arriving in proper XML
        format.

        :param msg:
        :return: parsed_msg
        """
        try:
            root = ElementTree.fromstring(msg)
        except ElementTree.ParseError:
            raise ParseError('Unable to parse msg')

        blob1 = root.find('blob1')
        data = ''.join(blob1.text.split())

        if len(data) != self._blob_len:
            raise ParseError('Incorrect number of bytes in msg data')

        # convert hex values to decimal

        msg_count = int(data[0:2], 16)
        veh_id = data[2:10]
        h = ops.verify(int(data[10:12], 16), 0, 23)
        m = ops.verify(int(data[12:14], 16), 0, 59)
        s = ops.verify(int(data[14:18], 16), 0, 60000)  # ms
        lat = ops.verify(ops.twos_comp(int(data[18:26], 16), 32), -900000000, 900000000) * 1e-7
        lon = ops.verify(ops.twos_comp(int(data[26:34], 16), 32), -1799999999, 1800000000) * 1e-7
        heading = ops.verify(int(data[34:38], 16), 0, 28799) * 0.0125
        speed = ops.verify(int(data[38:42], 16), 0, 8190)  # m/s
        lane = int(data[42:44], 16)
        veh_len = ops.verify(int(data[44:48], 16), 0, 16383) * 0.01  # m
        max_accel = ops.verify(int(data[48:52], 16), 0, 2000) * 0.01  # m/s^2
        max_decel = ops.verify(int(data[52:56], 16), 0, 2000) * -0.01  # m/s^2
        served = int(data[56:58], 16)

        if served == 1:
            raise ParseError('vehicle {} already has a trajectory'.format(veh_id))

        return {
            'msg_count': msg_count,
            'veh_id': veh_id,
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

