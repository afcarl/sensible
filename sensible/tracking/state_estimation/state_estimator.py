import os
import warnings

import numpy as np
import scipy.linalg

from sensible.tracking.state_estimation.radar_track_cfg import RadarTrackCfg
from sensible.util import ops
from sensible.util import time_stamp as ts

warnings.filterwarnings('ignore', category=FutureWarning)


class StateEstimator(object):
    """
    Super class for state estimation. Presents a common
    interface that can be used by the TrackSpecialist for any
    specific implementation.

    """

    def __init__(self, fused_track, sliding_window, stationary_R, use_bias_estimation):
        self.y = []  # messages
        self.x_k = []  # filtered track state
        self.y_k = []  # filtered measurement
        self.x_k_fused = []  # result of the covariance intersection algorithm
        self.t = []  # time stamps
        self.stationary_R = stationary_R
        self.fused_track = fused_track
        self.sliding_window = sliding_window
        self.use_bias_estimation = use_bias_estimation
        self.no_step = False

    def get_latest_message(self):
        """
        Returns the latest message
        :return:
        """
        t = self.t[-1]
        time = t if t is not None else ts.unavailable()
        return self.y[-1], time

    def state(self, window=1, get_unfused=False):
        """Return the latest Kalman Filter prediction of the state, and the timestamp."""
        t = self.t[-window:]
        time = ops.replace_none(t, ts.unavailable())
        if not self.fused_track or None in self.x_k_fused[-window:] or get_unfused:
            return self.x_k[-window:], time
        else:
            return self.x_k_fused[-window:], time

    def measurement(self, window=1):
        """Return the latest Kalman Filter prediction of the measurement, and the timestamp."""
        t = self.t[-window:]
        time = ops.replace_none(t, ts.unavailable())
        return self.y_k[-window:], time

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
            if len(self.y) >= 2 and len(self.x_k) == 0:
                self.x_k.append(self.init_state())
                self.x_k_fused.append(None)
                self.no_step = True

    def save_measurement(self, destination):
        yk, t = self.measurement()
        cov = self.measurement_residual_covariance()
        ops.dump({'time': t.to_string(), 'm': yk, 'cov': cov},
                 os.path.join(destination, 'kf-measurement-', t.to_fname_string(), '.pkl'))

    def save_state(self, destination):
        raise NotImplementedError
        xk, t = self.state()
        #cov = self.
        ops.dump({'time': t.to_string(), 'm': xk, 'cov': cov},
                 os.path.join(destination, 'kf-state-', t.to_fname_string(), '.pkl'))

    def to_string(self):
        kf_state, t = self.measurement()
        kf_state = kf_state[0]
        t = t[0]

        if type(t) is not str:
            t = t.to_string()

        kf_log_str = t + ','

        # For Radar
        if np.shape(kf_state)[0] == 2:
            kf_log_str += 'NaN,NaN,'

        for i in range(np.shape(kf_state)[0]):
            kf_log_str += str(kf_state[i]) + ','

        m, _ = self.get_latest_message()

        msg_log_str = t + ','

        # For Radar
        if np.shape(kf_state)[0] == 2:
            msg_log_str += 'NaN,NaN,'

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
        raise NotImplementedError
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
        s2, ts2 = track.state_estimator.state(window=self.sliding_window)
        p2 = track.state_estimator.P
        K2 = track.state_estimator.K

        t = self.t[-self.sliding_window:]
        time = ops.replace_none(t, ts.unavailable())

        t1 = ''
        t2 = ''
        for i in range(self.sliding_window):
            t1 += time[i].to_string() + ', '
            t2 += ts2[i].to_string() + ', '

        return self.n_scan_mahalanobis(s2=s2, p2_=p2, K2_=K2), t1, t2

    def init_state(self):
        raise NotImplementedError

    def n_scan_mahalanobis(self, s2, p2_, K2_):
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

    def parse_msg(self, msg, stationary_R):
        raise NotImplementedError
