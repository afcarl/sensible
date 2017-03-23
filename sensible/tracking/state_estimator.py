class TimeStamp:

    def __init__(self, h, m, s):
        self.h = h
        self.m = m
        self.s = s

    def to_string(self):
        return "{}:{}:{}".format(self.h, self.m, self.s)


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
        self.k = -1  # current time step

    def get_latest_measurement(self):
        """
        Returns the latest measurement
        :return:
        """
        if -1 < self.k < len(self.y):
            t = self.t[self.k]
            t_string = t.to_string() if t is not None else "UNAVAILABLE"
            return self.y[self.k], t_string
        else:
            return None, None

    def predicted_state(self):
        """Return the latest Kalman Filter prediction of the state, and the timestamp."""
        if -1 < self.k < len(self.x_k):
            t = self.t[self.k]
            t_string = t.to_string() if t is not None else "UNAVAILABLE"
            return self.x_k[self.k], t_string
        else:
            return None, None

    def predicted_state_covariance(self):
        """"Return the estimated state covariance
        """
        raise NotImplementedError

    def store(self, msg):
        self.k += 1
        if msg is None:
            self.y.append(None)
            self.t.append(None)
        else:
            self.y.append(self.parse_msg(msg))
            self.t.append(TimeStamp(msg['h'], msg['m'], msg['s']))
            if self.k == 0:
                self.x_k.append(self.y[self.k])

    def step(self):
        """One iteration of a discrete-time filtering algorithm.
        Uses the latest message saved by calling self.store(msg).
        """
        raise NotImplementedError

    def parse_msg(self, msg):
        """Converts a sensor msg into a measurement usable by the
        filtering algorithm."""
        raise NotImplementedError

