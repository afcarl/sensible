from __future__ import division

import socket
import time

from sensible.util import ops
from sensible.sensors.sensible_threading import StoppableThread


class SensorEmulator(StoppableThread):
    """Utility class for emulating a DSRC radio. Used for testing."""
    def __init__(self, port, pub_freq, file_names, delim=None, loop=True, delay=0, name="RadioEmulator"):
        """
        Constructor for SensorEmulator

        If using multiple files, make sure to increase the pub_freq correspondingly.
        There is 1 socket to send out all messages, so e.g., if there are 2 "vehicles",
        the pub frequency should be around 30-40 Hz instead of, say, 20 Hz for 1 vehicle

        Args:
            :param port:
            :param pub_freq:
            :param file_names:  a list of file names each containing DSRC messages for a trajectory
            :param delim:  the delimiter separating DSRC messages in the files
            :param loop:   Sensor mode where a single message in the first file is sent out repeatedly
            :param delay:   # of seconds to wait before starting to publish messages
            :param name:

        """
        super(SensorEmulator, self).__init__(name)
        self._port = port
        self._pub_freq = pub_freq
        self._fname = file_names
        self._delim = delim
        self._loop = loop
        self._delay = delay

        if self._loop:
            assert len(self._fname) == 1, "Provide only 1 file for Looping mode"

        # UDP port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)

    def run(self):
        """
        Parse a file containing csm messages delimited by
        delim. Send each at self._pub_freq and exit after the last msg.

        :return:
        """
        time.sleep(self._delay)

        msgs = []
        for f in self._fname:
            csm_file = open(f, 'r')
            if self._delim is not None:
                msgs.append(csm_file.read().split(self._delim))
            else:
                msgs.append(csm_file.read())
            csm_file.close()

        if self._loop:
            msg = msgs[0]
            while not self.stopped():
                self._socket.sendto(msg, ("localhost", self._port))
                time.sleep(1 / self._pub_freq)

            self._socket.close()
        else:

            flattened_msgs = ops.merge_n_lists(msgs)

            for i in flattened_msgs:
                if self.stopped():
                    break
                if i == "":
                    continue
                self._socket.sendto(i, ("localhost", self._port))
                time.sleep(1 / self._pub_freq)
            self._socket.close()

        print("  [*] {} finished sending messages...".format(self.name))
