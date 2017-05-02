from sensible.sensors.sensible_threading import SerialThread, StoppableThread
import sensible.util.ops as ops
from sensible.tracking.vehicle_type import VehicleType
from sensible.tracking.radar_track_cfg import RadarTrackCfg
from datetime import datetime

import time
import utm
import os

from collections import deque


class RadarSerial(SerialThread):
    def __init__(self, port, baud, radar_lat, radar_lon, mode="Tracking", lane=2, verbose=False, name="Radar"):
        super(RadarSerial, self).__init__(port, baud, name=name)
        self._verbose = verbose
        self.queue = deque()
        self._lane = lane
        self.mode = mode
        self.x, self.y, self.zone, self.letter = utm.from_latlon(radar_lat, radar_lon)
        self.msg_count = 0

        t = time.localtime()
        timestamp = time.strftime('%m-%d-%Y_%H%M', t)
        self.logger = open(os.path.join('logs', "msgLog_" + timestamp + ".csv"), 'wb')
        #self._synchronizer = RadarSynchronizer(self._queue, self._local_port, self.topic(), self._verbose)

    @staticmethod
    def topic():
        return "RadarSerial"

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

        speed = -msg['xVel']
        if speed < 4 or speed > 21:
            return None
        else:
            return {
                'id': msg['objID'],
                'h': h,
                'm': m,
                's': s,
                'xPos': self.x - msg['yPos'],
                'yPos': self.y + msg['xPos'],
                'speed': speed,  # accept 14 mph to 45 mph ~
                'veh_len': msg['objLength'],
                'lane': self._lane,
                'max_accel': 5,
                'max_decel': -5,
                'objZone': msg['objZone']
            }

    def add_to_queue(self, msg):
        """If the queue doesn't contain an identical message, add msg to the queue."""
        for queued_msg in list(self.queue):
            if queued_msg['id'] == msg['id'] and queued_msg['s'] == msg['s']:
                # Found a duplicate
                return
        self.queue.append(msg)

    def push(self, msg):
        self.msg_count += 1
        """Process incoming data. Overrides StoppableThread's push method."""
        for val in msg:
            res = self.parse(val)
            if res is not None:
                #self.logger.write()
                self.add_to_queue(res)