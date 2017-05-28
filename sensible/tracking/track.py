from sensible.tracking.track_state import TrackState
from sensible.tracking.kalman_filter import KalmanFilter
import sensible.util.time_stamp as ts
from sensible.sensors import DSRC


class Track(object):
    """Maintains state of a track and delegates state updates to a
    state estimator."""
    def __init__(self, dt, first_msg, sensor, n_scan, fusion_method=None):
        self.n_consecutive_measurements = 0
        self.n_consecutive_missed = 0
        self.received_measurement = False
        self.served = False
        self.fused_track_ids = []  # the track id of the other track fused with this one
        self.fusion_method = fusion_method

        self.veh_id = first_msg['id']

        self.track_state = TrackState.UNCONFIRMED
        self.sensor = sensor

        self.state_estimator = KalmanFilter(sensor.get_filter(dt), n_scan)

        # TODO: make an estimated value
        self.lane = first_msg['lane']
        self.veh_len = first_msg['veh_len']
        self.max_accel = first_msg['max_accel']
        self.max_decel = first_msg['max_decel']

        self.type = sensor.get_default_vehicle_type(id=self.veh_id)

    def step(self):
        """Carry out a single forward recursion of the state estimation."""
        self.state_estimator.step()

    def fuse_estimates(self, tracks):
        """Fuse this track estimates with the current estimates from argument track."""
        # compile states and covariances
        mu = []
        sigma = []
        s, t = self.state_estimator.state(get_unfused=True)
        p = self.state_estimator.P
        mu.append(s[0])
        sigma.append(p[-1])

        for track in tracks:
            s, t = track.state_estimator.state(get_unfused=True)
            mu.append(s[0])
            sigma.append(track.state_estimator.P[-1])
        fused_mu, fused_sigma = self.fusion_method(mu, sigma)
        self.state_estimator.x_k_fused.append(fused_mu)

    def fuse_empty(self):
        self.state_estimator.x_k_fused.append(None)
        # post-condition should always hold so these two arrays stay aligned
        assert len(self.state_estimator.x_k_fused) == len(self.state_estimator.x_k)

    def store(self, new_msg, track_list):
        """
        Pass a new message onto the state estimator and update state of the Track to reflect this.
        :param new_msg:
        :param track_list
        :return:
        """
        self.state_estimator.store(new_msg, ts.TimeStamp(new_msg['h'], new_msg['m'], new_msg['s']))
        self.received_measurement = True
        self.n_consecutive_measurements += 1
        self.n_consecutive_missed = 0
        self.lane = new_msg['lane']
        
        if self.served and self.sensor == DSRC.DSRC and new_msg['served'] == 0:
            self.served = False
            if self.state_estimator.fused_track:
                for fused_track_id in self.fused_track_ids:
                    track_list[fused_track_id].served = False							

        if not self.served and self.sensor == DSRC.DSRC and new_msg['served'] == 1:
            self.served = True
            if self.state_estimator.fused_track:
                for fused_track_id in self.fused_track_ids:
                    track_list[fused_track_id].served = True

