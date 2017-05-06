import numpy as np
import scipy.linalg
from sensible.util import ops
from sensible.util import time_stamp as ts
import os


class StateEstimator(object):
    """
    Super class for state estimation. Presents a common
    interface that can be used by the TrackSpecialist for any
    specific implementation.

    """

    def __init__(self, fused_track):
        self.y = []  # messages
        self.x_k = []  # filtered track state
        self.y_k = []  # filtered measurement
        self.x_k_fused = []  # result of the covariance intersection algorithm
        self.t = []  # time stamps
        self.fused_track = fused_track

    def get_latest_message(self):
        """
        Returns the latest message
        :return:
        """
        t = self.t[-1]
        time = t if t is not None else ts.unavailable()
        return self.y[-1], time

    def state(self, get_unfused=False):
        """Return the latest Kalman Filter prediction of the state, and the timestamp."""
        t = self.t[-1]
        time = t if t is not None else ts.unavailable()
        if not self.fused_track or self.x_k_fused[-1] is None or get_unfused:
            return self.x_k[-1], time
        else:
            return self.x_k_fused[-1], time

    def measurement(self):
        """Return the latest Kalman Filter prediction of the measurement, and the timestamp."""
        t = self.t[-1]
        time = t if t is not None else ts.unavailable()
        return self.y_k[-1], time

    def store(self, msg=None, time=None):
        if msg is None:
            self.y.append(msg)
            self.t.append(time)
        else:
            self.y.append(self.parse_msg(msg))
            self.t.append(time)
            if len(self.x_k) == 0:
                self.x_k.append(self.y[-1])
                self.x_k_fused.append(None)

    def save_measurement(self, destination):
        yk, t = self.measurement()
        cov = self.measurement_residual_covariance()
        ops.dump({'time': t.to_string(), 'm': yk, 'cov': cov},
                 os.path.join(destination, 'kf-measurement-', t.to_fname_string(), '.pkl'))

    def save_state(self, destination):
        xk, t = self.state()
        cov = self.process_covariance()
        ops.dump({'time': t.to_string(), 'm': xk, 'cov': cov},
                 os.path.join(destination, 'kf-state-', t.to_fname_string(), '.pkl'))

    def to_string(self, get_unfused=False):
        kf_state, t = self.state(get_unfused=get_unfused)

        if type(t) is not str:
            t = t.to_string()

        kf_log_str = t + ','
        for i in range(np.shape(kf_state)[0]):
            kf_log_str += str(kf_state[i]) + ','

        m, _ = self.get_latest_message()

        msg_log_str = t + ','
        if m is not None:
            for i in range(np.shape(m)[0]):
                msg_log_str += str(m[i]) + ','
        else:
            for i in range(np.shape(self.y_k[0])[0]):
                msg_log_str += 'NaN,'

        return kf_log_str, msg_log_str

    def mahalanobis(self, s, P, ts2=None):
        """
        Compute the track-to-track or measurement-to-track mahalanobis distance
        between track state or measurement `s` and the estimated state of this track

        :param s: measurement [x, xdot, y, ydot]
        :param P: covariance of s
        :return: the M distance
        """
        # TODO: Add cross-cov terms
        ss, ts1 = self.state()

        PP = self.process_covariance()

        if np.shape(PP)[0] == 4:
            PP = PP[2:4, 2:4]

        if np.shape(P)[0] == 4:
            P = P[2:4, 2:4]

        if np.shape(ss)[0] == 4:
            ss = ss[2:4]

        if np.shape(s)[0] == 4:
            s = s[2:4]

        #print('Track A state: {}, Track B state: {}'.format(s, ss))
        dx = s - ss
        return np.matmul(dx.T, np.matmul(scipy.linalg.inv(PP + P), dx)), ts1.to_string(), ts2.to_string()

    def measurement_residual_covariance(self):
        raise NotImplementedError

    def step(self):
        """One iteration of a discrete-time filtering algorithm.
        Uses the latest message saved by calling self.store(msg).
        """
        raise NotImplementedError

    def process_covariance(self):
        raise NotImplementedError

    def parse_msg(self, msg):
        raise NotImplementedError
