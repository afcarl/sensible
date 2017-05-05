from __future__ import division

import socket
import time
import pandas as pd

from sensible.util import ops
from sensible.sensors.sensible_threading import StoppableThread


class RadarEmulator(StoppableThread):
    """Utility class for emulating a DSRC radio. Used for testing."""
    def __init__(self, radar, pub_freq, fname, name="RadioEmulator"):
        super(RadarEmulator, self).__init__(name)
        self._radar = radar
        self._pub_freq = pub_freq
        self._fname = fname

        # UDP port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)

    def run(self):
        """
        Parse a file containing csm messages delimited by
        delim. Send each at self._pub_freq and exit after the last msg.

        :return:
        """
        df = pd.DataFrame.from_csv(self._fname, sep=' ', index_col=None)
        df['Time_s'] = pd.to_datetime(df['Time_s'], format="%H:%M:%S:%f")
        df = df.set_index('Time_s')
        res = df.index.get_duplicates()

        for i in range(len(res)):
            if self.stopped():
                break
            msgs = []
            radar_hits = df[df.index == res[i]]
            for index, row in radar_hits.iterrows():
                msg = {
                    'TimeStamp': {'h': index.hour, 'm': index.minute, 's': index.microsecond},
                    'objZone': -1,
                    'objID': row['Object_ID'],
                    'xPos': row['x_Point1'],
                    'yPos': row['y_Point1'],
                    'objLength': row['Length'],
                    'xVel': row['Speed_x'],
                    'yVel': row['Speed_y']
                }
                msgs.append(msg)
            self._radar.push(msgs)
            time.sleep(1. / self._pub_freq)

        print("  [*] {} finished sending messages...".format(self.name))
