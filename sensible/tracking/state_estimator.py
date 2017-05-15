import numpy as np
import scipy.linalg
from sensible.tracking.radar_track_cfg import RadarTrackCfg
from sensible.util import ops
from sensible.util import time_stamp as ts
import os


class StateEstimator(object):
    """
    Super class for state estimation. Presents a common
    interface that can be used by the TrackSpecialist for any
    specific implementation.

    """

    def __init__(self, fused_track, stationary_R):
        self.y = []  # messages
        self.x_k = []  # filtered track state
        self.y_k = []  # filtered measurement
        self.x_k_fused = []  # result of the covariance intersection algorithm
        self.t = []  # time stamps
        self.stationary_R = stationary_R
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
            if self.stationary_R:
                msg_ = self.parse_msg(msg, self.stationary_R)
            else:
                msg_, x_rms, y_rms = self.parse_msg(msg, self.stationary_R)
                self.update_measurement_covariance(x_rms, y_rms)
            self.y.append(msg_)
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

    def TTMA(self, m):
        """
        Statistical distance between a track and a radar measurement
        :param m: measurement
        :return:
        """
        s, ts = self.state()
        R = RadarTrackCfg(0.1).R
        dx = s - m
        P = self.process_covariance()
        return np.matmul(dx.T, np.matmul(scipy.linalg.inv(P + R), dx))

    def TTTA(self, track):
        """
        Compute the track-to-track or measurement-to-track mahalanobis distance
        between track state or measurement `s` and the estimated state of this track

        :param track:
        :return: the M distance, time stamps of comparison
        """
        s2, ts2 = track.state_estimator.state()
        p2 = track.state_estimator.process_covariance()
        K2 = track.state_estimator.K

        s1, ts1 = self.state()
        p1 = self.process_covariance()
        return self.mahalanobis_(s1=s1, p1=p1, s2=s2, p2=p2, K=K2), ts1.to_string(), ts2.to_string()

    def mahalanobis_(self, s1, p1, s2, p2, K):
        raise NotImplementedError

    def update_measurement_covariance(self, x_rms, y_rms):
        raise NotImplementedError

    def measurement_residual_covariance(self):
        raise NotImplementedError

    def step(self):
        """One iteration of a discrete-time filtering algorithm.
        Uses the latest message saved by calling self.store(msg).
        """
        raise NotImplementedError

    def process_covariance(self):
        raise NotImplementedError

    def parse_msg(self, msg, stationary_R):
        raise NotImplementedError
