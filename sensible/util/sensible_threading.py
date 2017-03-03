from __future__ import absolute_import
import threading
import socket
from sensible.util.exceptions import ParseError


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, name):
        super(StoppableThread, self).__init__(name=name)
        self._stopper = threading.Event()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def stop(self):
        """Stop the DSRC thread."""
        self.stop_thread()
        self.join()

    def stop_thread(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.is_set()


class SensorThread(StoppableThread):
    """Used for receiving data measurements from a sensor."""

    def __init__(self, name, msg_len):
        super(SensorThread, self).__init__(name)
        self._msg_len = msg_len

    def run(self):
        """Main method for Stoppable thread"""
        while not self.stopped():
            try:
                msg, address = self._sock.recvfrom(self._msg_len)
            except socket.error:
                continue

            try:
                self.push(msg)
            except ParseError as e:
                print(e.message)
                continue

        self._sock.close()

    def push(self, msg):
        """
        Push the msg through the processing pipeline.

        Needs to be defined by the subclass
        """
        raise NotImplementedError

    @staticmethod
    def topic():
        """Force all sensors to make accessible the topic of the
        message they are publishing."""
        raise NotImplementedError
