import time
from datetime import datetime

import utm

from collections import deque

from sensible.tracking.radar_track_cfg import RadarTrackCfg
from sensible.tracking.vehicle_type import VehicleType
from sensible.util import ops

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class Radar:
    """
    Thread that listens for incoming Radar messages and pre-processes them.
    Radar messages are "asynchronous"
    """

    def __init__(self, mode, lane, radar_lat, radar_lon, verbose=False):
        self._queue = deque()
        self._mode = mode
        self._verbose = verbose
        self._lane = lane
        self.x, self.y, self.zone, self.letter = utm.from_latlon(
            radar_lat, radar_lon)

        self.count = 0

    @property
    def queue(self):
        return self._queue

    @staticmethod
    def topic():
        return "Radar"

    @staticmethod
    def get_filter(dt):
        return RadarTrackCfg(dt)

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
    def get_default_vehicle_type(**kwargs):
        return VehicleType.UNKNOWN

    def parse(self, msg):
        # TODO: add lane number to msg
        zone = msg['objZone']
        if self._mode == "Zone" and zone == -1:
            raise ValueError("Expected a zone number > 0")
        if self._mode == "Tracking" and zone >= 0:
            raise ValueError("Expected a zone number of -1")

        #timestamp = msg['TimeStamp']
        # dt = datetime.utcnow()
        # h = dt.hour
        # m = dt.minute
        # s = dt.second * 1000 + round(dt.microsecond / 1000)

        speed = -msg['xVel']
        if speed < 4 or speed > 21:
            return None
        else:
            return {
                'id': msg['objID'],
                'h': msg['TimeStamp']['h'],
                'm': msg['TimeStamp']['m'],
                's': msg['TimeStamp']['s'],
                'xPos': self.x - msg['yPos'],
                'yPos': self.y + msg['xPos'],
                'speed': speed,  # accept 14 mph to 45 mph ~
                'veh_len': msg['objLength'],
                'lane': self._lane,
                'max_accel': 5,
                'max_decel': -5,
                'objZone': msg['objZone']
            }

    def push(self, msgs):
        """Process incoming data. Overrides StoppableThread's push method."""
        self.count += len(msgs)
        for msg in msgs:
            res = self.parse(msg)
            if res is not None:
                #self.logger.write()
                self.add_to_queue(res)

    def add_to_queue(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in list(self._queue):
            if queued_msg['id'] == msg['id'] and queued_msg['s'] == msg['s']:
                # Found a duplicate
                return
        self._queue.append(msg)
