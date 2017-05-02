import scipy.optimize as opt
import scipy.linalg
import numpy as np


def covariance_intersection(means, covariances):
    """
    The mean estimates and covariance estimates from the
    state estimators from N sensors.

    Produces a fused mean and covariance estimate.

    Expects 4x4 or 2x2 covariance matrices. Fuses the upper left quadrant
    and lower right quadrant separately (e.g., for state [x, xdot, y, ydot])

    :param means:
    :param covariances:
    :return:
    """
    inv_cov_lower = []
    inv_cov_upper = []
    for cov in covariances:
        if np.shape(cov)[0] == 4:
            inv_cov_lower.append(scipy.linalg.inv(cov[2:4, 2:4]))
            inv_cov_upper.append(scipy.linalg.inv(cov[0:2, 0:2]))
        else:
            inv_cov_lower.append(scipy.linalg.inv(cov))
    means_lower = []
    means_upper = []
    for mean in means:
        if np.shape(mean)[0] == 4:
            means_lower.append(mean[2:4])
            means_upper.append(mean[0:2])
        else:
            means_lower.append(mean)

    def cumsum(x, y, z=None):
        s = 0
        for jj in range(len(x)):
            if z is not None:
                s += np.matmul(x[jj] * y[jj], z[jj])
            else:
                s += x[jj] * y[jj]
        return s

    inv_cov_intersection = np.zeros((4, 4))
    inv_cov = [inv_cov_lower, inv_cov_upper]
    means_list = [means_lower, means_upper]
    fused_mean = np.zeros(4)

    for i in range(2):
        if len(inv_cov[i]) > 1:
            # solve for optimal combination parameters
            # the objective function is the determinant (or trace?) of the inverse of the
            # convex combination of the information (inverse cov) from state estimates from
            # the two sensors
            x0 = 1./len(means) * np.ones(len(means))

            res = opt.minimize(lambda x: scipy.linalg.det(scipy.linalg.inv(cumsum(x, inv_cov[i]))),
                               x0=x0,
                               method='SLSQP',
                               constraints=({'type': 'ineq', 'fun': lambda x: x},  # x >= 0
                                            {'type': 'eq', 'fun': lambda x: 1 - np.sum(x)}))  # 1 - x >= 0 == x <= 1

            w = res.x
            if i == 0:
                inv_cov_intersection[2:4, 2:4] = cumsum(w, inv_cov[i])
                fused_mean[2:4] = np.matmul(scipy.linalg.inv(inv_cov_intersection[2:4, 2:4]),
                                  cumsum(w, inv_cov[i], means_list[i]))
            else:
                inv_cov_intersection[0:2, 0:2] = cumsum(w, inv_cov[i])
                fused_mean[0:2] = np.matmul(scipy.linalg.inv(inv_cov_intersection[0:2, 0:2]),
                                  cumsum(w, inv_cov[i], means_list[i]))
        else:
            if i == 0:
                inv_cov_intersection[2:4, 2:4] = inv_cov[i][0]
                fused_mean[2:4] = means_list[i][0]
            else:
                inv_cov_intersection[0:2, 0:2] = inv_cov[i][0]
                fused_mean[0:2] = means_list[i][0]

    return fused_mean, inv_cov_intersection
