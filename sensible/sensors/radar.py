import zmq
import time

from collections import deque

from sensible.sensors.sensible_threading import StoppableThread
from sensible.sensors.sensible_threading import SensorThread
from sensible.sensors.DSRC import DSRC
from sensible.tracking.radar_track_cfg import RadarTrackCfg
from sensible.util import ops

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class Radar(SensorThread):
    """
    Thread that listens for incoming Radar messages and pre-processes them.
    Radar messages are "asynchronous"
    """
    def __init__(self, ip_address, remote_port, local_port, verbose=False, name="Radar"):
        super(Radar, self).__init__(ip_address, remote_port, msg_len=277, name=name)
        self._queue = deque()
        self._context = zmq.Context()
        self._publisher = self._context.socket(zmq.PUB)
        # bind to tcp port _local_port
        self._publisher.bind("tcp://*:{}".format(local_port))
        self._local_port = local_port
        self._verbose = verbose

        class RadarSynchronizer(StoppableThread):
            """Publish messages from a thread-safe queue"""

            def __init__(self, queue, port, topic, name="RadarSynchronizer"):
                super(RadarSynchronizer, self).__init__(name)
                self._publish_freq = 50  # Hz
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

        self._synchronizer = RadarSynchronizer(self._queue, self._local_port, self.topic())

    @staticmethod
    def topic():
        return "Radar"

    @staticmethod
    def get_filter(dt):
        return RadarTrackCfg(dt)

    def stop(self):
        """Overrides the super class stop method, so explicitly
        call it here."""
        self._synchronizer.stop()
        super(Radar, self).stop()

    def connect(self):
        super(Radar, self).connect()

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

    def parse(self, msg):
        # TODO: throw away messages that don't satisfy gating properties
        # using ops.verify
        raise NotImplementedError
