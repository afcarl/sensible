from sensible.sensors.sensible_threading import SensorThread
import sensible.util.ops as ops
import sensible.util.time_stamp as ts


try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle

import zmq

from collections import deque as queue


class RadarZoneDetection(SensorThread):
    def __init__(self, ip_address, remote_port, local_port, verbose=False, name="Radar"):
        super(RadarZoneDetection, self).__init__(ip_address, remote_port, msg_len=277, name=name)
        self._verbose = verbose
        self._queue = queue
        self._context = zmq.Context()
        self._publisher = self._context.socket(zmq.PUB)
        # bind to tcp port _local_port
        self._publisher.bind("tcp://*:{}".format(local_port))

    def push(self, msg):
        """Process incoming data. Overrides StoppableThread's push method."""
        m = self.parse(msg)
        self._publisher.send_string("{} {}".format(self.topic(), pickle.dumps(m)))
        ops.show(' [RadarZoneDetection] Sent msg for veh: {} at second: {}'.format(m['id'],
                                                                                   m['s']), self._verbose)

    @staticmethod
    def topic():
        return "RadarZoneDetection"

    @staticmethod
    def get_filter(dt):
        pass

    def parse(self, msg):
        raise NotImplementedError

    @staticmethod
    def bsm(msg):
        """
        Generate a BSM from the message
        :param msg:
        :return:
        """
        # TODO: get timestamp from message
        timestamp = msg['ts']

        # "{},{},{},{},{},{},{},{}".format(
        #     track_id,
        #     timestamp.h,
        #     timestamp.m,
        #     timestamp.s,
        #     x_hat[0],  # meters easting
        #     x_hat[2],  # meters northing
        #     np.round(np.sqrt(np.power(x_hat[1], 2) + np.power(x_hat[3], 2)), 3),  # m/s
        #     # self._lane,
        #     # self._veh_len,
        #     # self._max_accel,
        #     # self._max_decel,
        #     self.served
        # )