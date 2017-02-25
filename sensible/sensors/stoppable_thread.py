import threading


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, name):
        super(StoppableThread, self).__init__(name=name)
        self._stopper = threading.Event()

    def stop_thread(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.is_set()
