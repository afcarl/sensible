class StateEstimator(object):
    """
    Super class for state estimation. Presents a common
    interface that can be used by the TrackSpecialist for any
    specific implementation.

    """
    def __init__(self):
        self.y = []  # measurements

        self.x_k = []  # predicted track state
        self.y_k = []  # predicted measurement

        self.t = []  # time stamps
        self.k = 0  # current time step

    def get_latest_measurement(self):
        return self.y[self.k] if self.k > 0 else None

    def store(self, msg):
        self.y.append(self.parse_msg(msg))

    def step(self):
        """One iteration of a discrete-time filtering algorithm.
        Uses the latest message saved by calling self.store(msg).
        """
        raise NotImplementedError

    def parse_msg(self, msg):
        """Converts a sensor msg into a measurement usable by the
        filtering algorithm."""
        raise NotImplementedError

    def update_log(self, logger):
        """
        Write all track information to the file
        :param logger:
        :return:
        """
        pass
