import zmq
import time

from sensible.sensors.sensible_threading import SensorThread

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class Radar(SensorThread):
    """
    Thread that listens for incoming Radar messages and pre-processes them.
    Radar messages are "asynchronous"
    """
    def __init__(self, ip_address, remote_port, local_port, spam=1.0, name="Radar"):
        super(Radar, self).__init__(name, ip_address, remote_port, msg_len=0)

        self._spam = spam  # time in sec to repeatedly send out a new message

        self._context = zmq.Context()
        self._publisher = self._context.socket(zmq.PUB)
        # bind to tcp port _local_port
        self._publisher.bind("tcp://*:{}".format(local_port))


    @staticmethod
    def topic():
        return "Radar"

    def push(self, msg):
        """
        Parse the incoming message and forward to the track specialist

        :param msg:
        :return:
        """
        t_end = time.time() + self._spam

        while time.time() < t_end:
            self._publisher.send_string("{} {}".format(self.topic(), pickle.dumps(msg)))

    def connect(self):
        super(Radar, self).connect()
