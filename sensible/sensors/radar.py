import csv
import os
import time
from collections import deque
from datetime import datetime

import numpy as np
import utm

from sensible.tracking.state_estimation.radar_track_cfg import RadarTrackCfg
from sensible.tracking.vehicle_type import VehicleType

try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


class Radar:
    """
    Thread that listens for incoming Radar messages and pre-processes them.
    Radar messages are "asynchronous"
    """

    def __init__(self, mode, lane, radar_lat, radar_lon, orientation, clock_offset=0, record_csv=False, verbose=False):
        self._queue = deque()
        self._mode = mode
        self._verbose = verbose
        self._lane = lane
        self.x, self.y, self.zone, self.letter = utm.from_latlon(
            radar_lat, radar_lon)
        self.clock_offset = clock_offset
        self.rotation = np.array([[np.cos(np.deg2rad(360. - orientation)), -np.sin(np.deg2rad(360. - orientation))],
                                  [np.sin(np.deg2rad(360. - orientation)), np.cos(np.deg2rad(360. - orientation))]])

        if record_csv:
            t = time.localtime()
            timestamp = time.strftime('%m-%d-%Y_%H%M', t)
            radar_logger = open(os.path.join('logs', "radarLog_" + timestamp + ".csv"), 'wb')
            header = ['objMessage', 'objID', 'objLength', 'yVel', 'xVel', 'yPos', 'xPos', 'TimeStamp', 'objZone']
            self._logger = csv.DictWriter(radar_logger, fieldnames=header)
            self._logger.writeheader()
        else:
            self._logger = None

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

        return "{},{},{},{},{},{},{},{},{},{},{},{},{}".format(
            track_id,
            track.veh_id,
            t[0].h,
            t[0].m,
            t[0].s,
            '0',  # meters easting
            state[0][0],  # meters northing
            abs(state[0][1]),  # m/s
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
        # print(msg)
        # TODO: add lane number to msg
        zone = msg['objZone']
        if self._mode == "Zone" and zone == -1:
            raise ValueError("Expected a zone number > 0")
        if self._mode == "Tracking" and zone >= 0:
            raise ValueError("Expected a zone number of -1")

        if msg['xVel'] > -4 or msg['xVel'] < -21:  # 9 mph to 47 mph
            return None
        else:
            dt = datetime.utcnow()
            hour = dt.hour
            minute = dt.minute
            ms = int(dt.second * 1000 + round(dt.microsecond/1000))
            # #print('Radar correct time: {}:{}:{}'.format(h, m, s))
            # #print('Radar time: {}'.format(msg['TimeStamp']))
            # t = msg['TimeStamp'].split(':')
            # h = int(t[0])
            # m = int(t[1])
            # s = int(t[2])

            # apply rotation
            pos = np.array([[-msg['yPos']], [msg['xPos']]])
            pos_ = np.matmul(self.rotation, pos)

            vel = np.array([[-msg['yVel']], [msg['xVel']]])
            vel_ = np.matmul(self.rotation, vel)

            return {
                'id': int(msg['objID']),
                'h': hour,
                'm': minute,
                's': ms,
                'xPos': self.x + pos_[0, 0],
                'yPos': self.y + pos_[1, 0],
                'speed': vel_[1, 0],  # longitudinal speed
                'veh_len': msg['objLength'],
                'lane': self._lane,
                'max_accel': 3.048,
                'max_decel': -4.572,
                'objZone': msg['objZone']
            }

    def push(self, msgs):
        """Process incoming data. Overrides StoppableThread's push method."""
        for msg in msgs:
            if self._logger is not None:
                self._logger.writerow(msg)
            res = self.parse(msg)
            if res is not None:
                self.add_to_queue(res)

    def add_to_queue(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in list(self._queue):
            if queued_msg['id'] == msg['id'] and queued_msg['s'] == msg['s']:
                # Found a duplicate
                return
                # add X to the right side of the queue
        self._queue.append(msg)
