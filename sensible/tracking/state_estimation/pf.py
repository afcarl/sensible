import numpy as np
import scipy.stats
from sensible.tracking.state_estimation.state_estimator import StateEstimator
from collections import deque


class ParticleFilter(StateEstimator):
    """

    Measurment noise is GMM:

    Means: [[ 0.13282853 -1.45870104]
     [ 0.2473145  -3.36940746]]
    Covariances: [[[ 0.02395555  0.03301341]
      [ 0.03301341  0.58630483]]

     [[ 0.08044994  0.1920035 ]
      [ 0.1920035   1.6495695 ]]]
    Weights: [ 0.36320182  0.63679818]

    """
    def __init__(self, cfg, num_particles=5000, sliding_window=1, use_bias_estimation=True, fused_track=False):
        super(ParticleFilter, self).__init__(fused_track, sliding_window, fused_track, use_bias_estimation)
        self.state_dim = cfg.state_dim
        self.Q = cfg.Q
        self.F = cfg.F
        self.sensor_cfg = cfg
        self.P = deque(maxlen=sliding_window)
        self.P.append(self.sensor_cfg.P)
        self._num_particles = num_particles
        self._weights = np.zeros(self._num_particles)
        self._particles = None

    def create_gaussian_particles(self, mean, cov):
        # shape = (num_particles, state_dim)
        self._particles = np.random.multivariate_normal(mean, cov, size=(self._num_particles))

    def init_state(self):
        x = self.sensor_cfg.init_state(self.y[-1],
                                          self.y[-2], self.sensor_cfg.dt)
        self.create_gaussian_particles(x, self.sensor_cfg.P)
        return x

    def predict(self):
        """
        Create new particles by propagating old particles through dynamics
        :return:
        """
        # (num_particles, state_dim)
        self._particles = np.matmul(self.F, self._particles.T).T + \
                    np.random.multivariate_normal(np.zeros(self.state_dim),
                                                  self.Q, size=self._num_particles)
    def update(self, z):
        """
        Use measurements to compute weights - we set the proposal distribution
        q to be the prior. Hence, posterior/prior gives us the likelihood
        as the proposal distribution (i.e., the noisy measurement of the true belief)
        :return:

        Args:
            z: measurement vector, shape (4,)
        """
        self._weights.fill(1.)

        # for all N particles, generate vectors of dim measurement_dim with mean z and
        # noise added by sampling from the noise distribution
        if self.use_bias_estimation:
            bias_estimate = self.sensor_cfg.bias_estimate(z[2], np.deg2rad(z[3]))
            z[0:2] -= bias_estimate

        if self.sensor_cfg.motion_model == 'CV':
            x = self._particles[:, 0]
            y = self._particles[:, 2]
            x_dot = self._particles[:, 1]
            y_dot = self._particles[:, 3]
        elif self.sensor_cfg.motion_model == 'CA':
            x = self._particles[:, 0]
            y = self._particles[:, 3]
            x_dot = self._particles[:, 1]
            y_dot = self._particles[:, 4]

        theta_pred = np.arctan2(y_dot, x_dot)
        theta_pred[theta_pred < 0] += 2 * np.pi

        h = np.array([x, y, np.sqrt(x_dot ** 2 + y_dot ** 2), np.rad2deg(theta_pred)]).T
        # shape (N, measurement_dim, measurement_dim)
        R = self.sensor_cfg.batch_rotate_covariance(theta_pred)

        for i in range(self._num_particles):
            self._weights[i] *= scipy.stats.multivariate_normal(h[i], R[i]).pdf(z)
        self._weights += 1.e-300 # avoid round-off to zero
        self._weights /= sum(self._weights)  # normalize

    def resample(self):
        """
        Use the importance weights to replenish particles to avoid degeneracy
        :return:
        """
        cumulative_sum = np.cumsum(self._weights)
        cumulative_sum[-1] = 1.  # avoid round-off error
        indexes = np.searchsorted(cumulative_sum,
                                  np.random.random(self._num_particles))

        # resample according to indexes
        self._particles[:] = self._particles[indexes]
        self._weights.fill(1.0 / self._num_particles)

    def neff(self):
        return 1. / np.sum(np.square(self._weights))

    def estimate_state(self):
        """
        Return the estimated state given particles and weights
        :return:
        """
        mean = np.average(self._particles, weights=self._weights, axis=0)
        var = np.average((self._particles - mean) ** 2, weights=self._weights, axis=0)
        return mean, var

    def step(self):
        """
        One full step of the PF
        :return:
        """
        if len(self.x_k) < 1:
            return
        elif self.no_step:
            self.no_step = False
            return

        m, _ = self.get_latest_message()
        
        if abs(m[2]) < 0.8:
            self.x_k.append(self.x_k[-1])
            self.P.append(self.P[-1])

        # step the particles forward
        self.predict()

        # incorporate measurement
        self.update(m)

        # resample if too few effective particles
        if self.neff() < self._num_particles / 2:
            self.resample()

        x, P = self.estimate_state()
        self.x_k.append(x)
        self.P.append(P)
