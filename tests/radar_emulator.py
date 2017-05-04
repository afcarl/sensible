from __future__ import division

import socket
import time
import pandas as pd

from sensible.util import ops
from sensible.sensors.sensible_threading import StoppableThread


class RadarEmulator(StoppableThread):
    """Utility class for emulating a DSRC radio. Used for testing."""
    def __init__(self, port, pub_freq, fname, name="RadioEmulator"):
        """
        Args:
            :param port:
            :param pub_freq:
            :param fname:
            :param name:

        """
        super(RadarEmulator, self).__init__(name)
        self._port = port
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
            msgs = []
            radar_hits = df[df.index == res[i]]
            for val in radar_hits:
                msg = {
                    'TimeStamp': 0,
                    'objZone': -1,
                    'objID': val['Object_ID'],
                    'xPos': val['x_Point1'],
                    'yPos': val['y_Point1'],
                    'objLength': val['Length'],
                    'xVel': val['Speed_x'],
                    'yVel': val['Speed_y']
                }
                msgs.append(msg)

            self._socket.sendto(msg, ("localhost", self._port))
            time.sleep(1 / self._pub_freq)
        self._socket.close()

        print("  [*] {} finished sending messages...".format(self.name))
