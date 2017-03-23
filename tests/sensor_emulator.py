from __future__ import division

import socket
import time

from sensible.sensors.sensible_threading import StoppableThread


class SensorEmulator(StoppableThread):
    """Utility class for emulating a DSRC radio. Used for testing."""
    def __init__(self, port, pub_freq, file_name, delim=None, loop=True, delay=0, name="RadioEmulator"):
        super(SensorEmulator, self).__init__(name)
        self._port = port
        self._pub_freq = pub_freq
        self._fname = file_name
        self._delim = delim
        self._loop = loop
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
        time.sleep(self._delay)

        with open(self._fname, 'r') as f:

            # Send a single CSM, the contents of the file
            # until the thread is stopped
            if self._loop:

                csm = f.read()

                while not self.stopped():
                    self._socket.sendto(csm, ("localhost", self._port))
                    time.sleep(1 / self._pub_freq)

                self._socket.close()
            else:
                # Send each CSM in the file
                csm = f.read().split(self._delim)

                for i in csm:
                    if self.stopped():
                        break
                    if i == "":
                        continue
                    self._socket.sendto(i, ("localhost", self._port))
                    time.sleep(1 / self._pub_freq)
                self._socket.close()
            print("  [*] {} finished sending messages...".format(self.name))
