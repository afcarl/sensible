from __future__ import division

import zmq
import time

from sensible.sensors.sensible_threading import StoppableThread
import sensible.util.ops as ops

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class Synchronizer(StoppableThread):
    """Publish messages from a thread-safe queue"""

    def __init__(self, publish_freq, queue, port, topic, verbose=False, name="Synchronizer"):
        super(Synchronizer, self).__init__(name)
        self._publish_freq = publish_freq  # Hz
        self._queue = queue
        self._context = zmq.Context()
        self._publisher = self._context.socket(zmq.PUB)
        # bind to tcp port _local_port
        self._publisher.bind("tcp://*:{}".format(port))
        self._topic = topic
        self._verbose = verbose

    @property
    def queue(self):
        return self._queue

    def send(self):
        """If the queue is not empty, send the message stored at front of the queue.

        Here, the invariant is assumed to be that the queue only
        contains the unique message sent within a time frame of publish_freq seconds. The dictionary
        is pickled, so it should be un-pickled at the subscriber.

        Send 1 message from each unique DSRC_id in the queue
        """
        if len(self._queue) > 0:
            sent_ids = []
            for queued_msg in list(self._queue):
                if queued_msg['id'] not in sent_ids:
                    self._publisher.send_string("{} {}".format(self._topic, pickle.dumps(queued_msg)))
                    sent_ids.append(queued_msg['id'])

                    # ops.show('  [{}] Sent msg for veh: {} at {}:{}:{}\n'.format(self.name,
                    #                                                   queued_msg['id'],
                    #                                                   queued_msg['h'],
                    #                                                   queued_msg['m'],
                    #                                                   queued_msg['s']),
                    #          self._verbose)
            # drop all messages
            self._queue.clear()

    def run(self):
        period = 1 / self._publish_freq
        while not self.stopped():
            self.send()
            time.sleep(period)
