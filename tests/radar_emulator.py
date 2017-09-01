from __future__ import division

import socket
import time
from datetime import datetime
import pandas as pd

import tests.context

from sensible.sensors.sensible_threading import StoppableThread


class RadarEmulator(StoppableThread):
    """Utility class for emulating a DSRC radio. Used for testing."""
    def __init__(self, radar, pub_freq, fname, delay=0, name="RadioEmulator"):
        super(RadarEmulator, self).__init__(name)
        self._radar = radar
        self._pub_freq = pub_freq
        self._fname = fname
        self._delay = delay

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

        period = 1. / self._pub_freq

        time.sleep(self._delay)

        run_start = time.time()
        count = 0

        for i in range(len(res)):
            start = time.time()
            if self.stopped():
                break
            msgs = []
            radar_hits = df[df.index == res[i]]
            for index, row in radar_hits.iterrows():
                msg = {
                    'objMessage': "Track",
                    'TimeStamp': {'h': index.hour,
                                  'm': index.minute,
                                  's': int(index.second * 1000 + (index.microsecond / 1000))},
                    'objZone': -1,
                    'objID': row['Object_ID'],
                    'xPos': row['x_Point1'],
                    'yPos': row['y_Point1'],
                    'objLength': row['Length'],
                    'xVel': row['Speed_x'],
                    'yVel': row['Speed_y']
                }
                msgs.append(msg)
            count += len(msgs)
            self._radar.push(msgs)
            diff = time.time() - start
            time.sleep(period - diff)

        run_end = time.time()
        print("[{}] Sent {} messages in {} seconds, at {} msgs/sec...".format(self.name, count, run_end - run_start,
                                                                                count / (run_end - run_start)))

    # def run(self):
    #     """
    #     Parse a file containing csm messages delimited by
    #     delim. Send each at self._pub_freq and exit after the last msg.
    #
    #     :return:
    #     """
    #     df = pd.DataFrame.from_csv(self._fname, index_col=None)
    #     df = df.set_index('TimeStamp')
    #     res = df.index.get_duplicates()
    #
    #     period = 1. / self._pub_freq
    #
    #     time.sleep(self._delay)
    #
    #     run_start = time.time()
    #     count = 0
    #
    #     for i in range(len(res)):
    #         start = time.time()
    #         if self.stopped():
    #             break
    #         msgs = []
    #         radar_hits = df[df.index == res[i]]
    #         dt = datetime.utcnow()
    #         h = dt.hour
    #         m = dt.minute
    #         s = int(dt.second * 1000 + round(dt.microsecond / 1000))
    #
    #         for index, row in radar_hits.iterrows():
    #             msg = {
    #                 'TimeStamp': {'h': h,
    #                               'm': m,
    #                               's': s},
    #                 'objZone': row['objZone'],
    #                 'objID': row['objID'],
    #                 'xPos': row['xPos'],
    #                 'yPos': row['yPos'],
    #                 'objLength': row['objLength'],
    #                 'xVel': row['xVel'],
    #                 'yVel': row['yVel']
    #             }
    #             msgs.append(msg)
    #         count += len(msgs)
    #         self._radar.push(msgs)
    #         diff = time.time() - start
    #         time.sleep(period - diff)
    #
    #     run_end = time.time()
    #     print("[{}] Sent {} messages in {} seconds, at {} msgs/sec...".format(self.name, count, run_end - run_start,
    #                                                                             count / (run_end - run_start)))
