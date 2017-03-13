from sensible.tracking.kalman_filter import KalmanFilter
import numpy as np


def fake_msg():
    """Return a fake DSRC message for tests"""
    return {
        'msg_count': 0,
        'veh_id': '00000111',
        'h': 14,
        'm': 14,
        's': 14,
        'lat': 29.12123,
        'lon': -82.345234,
        'heading': 0,
        'speed': 20,
        'lane': 1,
        'veh_len': 15,
        'max_accel': 3.2,
        'max_decel': -3.2,
        'served': 0
    }


def test_instantiate_kf():
    """Test that the KF class can be instantiated with all
    members having valid default values."""
    kf = KalmanFilter(dt=0.2)


def test_parse_msg():
    """Test that a DSRC message is correctly parsed."""
    kf = KalmanFilter(dt=0.2)
    msg = fake_msg()

    expected_x_hat = 369121.1
    expected_y_hat = 3222164.79

    # test 45' heading from true north
    msg['heading'] = 45.0

    # speed is 20 m/s
    msg['speed'] = 20.0
    expected_x_hat_dot = -14.1420721227
    expected_y_hat_dot = 14.1421991245

    expected = np.array([expected_x_hat, expected_x_hat_dot, expected_y_hat, expected_y_hat_dot])
    result = kf.parse_msg(msg)

    assert np.allclose(result, expected, rtol=1e-03)

    # test 200' heading from true north
    msg['heading'] = 200.0

    expected_x_hat_dot = 6.8403120774
    expected_y_hat_dot = -18.79388546

    expected = np.array([expected_x_hat, expected_x_hat_dot, expected_y_hat, expected_y_hat_dot])
    result = kf.parse_msg(msg)

    assert np.allclose(result, expected, rtol=1e-03)
