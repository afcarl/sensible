import numpy as np


class ParticleFilter:
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
    def __init__(self, cfg, num_particles):
        self.state_dim = cfg.state_dim
        self.Q = cfg.Q
        self.F = cfg.F
        self._num_particles = num_particles
        self._particles = None
        self._weights = np.zeros(self._num_particles)

    def create_gaussian_particles(self, mean, cov):
        # shape = (num_particles, state_dim)
        self._particles = np.random.multivariate_normal(mean, cov, size=self.state_dim)

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
        """
        self._weights.fill(1.)

        # for all N particles, generate vectors of dim measurement_dim with mean z and
        # noise added by sampling from the noise distribution


    def resample(self):
        """
        Use the importance weights to replenish particles to avoid degeneracy
        :return:
        """

    def neff(self, weights):
        return 1. / np.sum(np.square(weights))

    def estimate_state(self):
        """
        Return the estimated state given particles and weights
        :return:
        """

    def step(self):
        """
        One full step of the PF
        :return:
        """