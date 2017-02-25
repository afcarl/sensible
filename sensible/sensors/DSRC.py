from __future__ import absolute_import

import zmq
import socket
import xml.etree.cElementTree as ElementTree
from collections import deque
from twisted.internet import task
from twisted.internet import reactor
import cPickle as pickle

from .stoppable_thread import StoppableThread
from ..util.exceptions import ParseError
from ..util import ops


class DSRC(StoppableThread):
    """Thread that listens for incoming DSRC radio messages and pre-processes them.

    """

    def __init__(self, ip_address, port, name="DSRC"):
        super(DSRC, self).__init__(name)
        self.ip_address = ip_address
        self.port = port
        self.msg_len = 277
        self.blob_len = 58
        self.publish_freq = 5  # Hz

        self.radio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.queue = deque()
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)

        self.synchronizer = task.LoopingCall(self.send)

    def connect(self):
        # open connection to incoming DSRC messages
        self.radio_sock.bind((self.ip_address, self.port))
        self.radio_sock.setblocking(0)

        # start publisher as a Twisted looping call
        self.publisher.bind("udp://localhost:6666")
        self.synchronizer.start(1. / self.publish_freq)
        reactor.run()

    def run(self):
        while not self.stopped():
            try:
                data, address = self.radio_sock.recvfrom(self.msg_len)
            except socket.error:
                continue

            try:
                self.push(self.parse(data))
            except ParseError:
                # Optionally log parse error messages
                continue

        self.radio_sock.close()

    def stop(self):
        self.stop_thread()
        self.join()

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

        if len(data) != self.blob_len:
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

    def push(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in self.queue:
            if msg['s'] == queued_msg['s']:
                return
        self.queue.append(msg)

    def send(self):
        """If the queue is not empty, send the message stored at front of the queue.

        Here, the invariant is assumed to be that the queue only
        contains the unique message sent within a time frame of 0.2 seconds. The dictionary
        is pickled, so it should be un-pickled at the subscriber.
        """
        if len(self.queue) > 1:
            self.publisher.send_string(pickle.dumps(self.queue.pop()))
