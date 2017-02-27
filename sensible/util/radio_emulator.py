from __future__ import division

from sensible.util.sensible_threading import StoppableThread
import socket
import time


class RadioEmulator(StoppableThread):
    """Utility class for emulating a DSRC radio. Used for testing."""
    def __init__(self, port, pub_freq, name="RadioEmulator"):
        super(RadioEmulator, self).__init__(name)
        self._port = port
        self._pub_freq = pub_freq

        # UDP port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)

    def run(self):
        with open("data/csm-nb.txt", 'r') as f:
            csm = f.read()

            while not self.stopped():
                self._socket.sendto(csm, ("localhost", self._port))
                time.sleep(1 / self._pub_freq)

        self._socket.close()
