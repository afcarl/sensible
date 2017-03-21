"""
Test the Kalman Filter with a full trajectory by simulating a radio
sending the messages in real time (20 Hz)
"""
import pytest
import time
import os

from tests.radio_emulator import RadioEmulator
from sensible.tracking.track_specialist import TrackSpecialist
from sensible.sensors.DSRC import DSRC


def get_track_specialist(sensor_port=6666, bsm_port=6667, run_for=20.0, frequency=5):
    """Return a standard TrackSpecialist object for testing."""
    topic_filters = ["DSRC", "Radar"]
    # p = tmpdir.mkdir("logs").join("test.csv")
    # Track logger
    t = time.localtime()
    log_dir = os.getcwd()
    timestamp = time.strftime('%m-%d-%Y_%H%M', t)
    p = open(os.path.join(log_dir, '..', 'logs', "trackLog_" + timestamp + ".csv"), 'wb')
    return TrackSpecialist(sensor_port, bsm_port, topic_filters, run_for, p, frequency)


def test_trajectory():
    radio = RadioEmulator(port=4200, pub_freq=20,
                          file_name="data/01-27-17-solarpark/GPS/Solar_UrbanNavi012717/suilog_1485534929.txt",
                          delim="CSM Tx...", loop=False, delay=2)

    remote_port = 4200
    local_port = 6666
    dsrc = DSRC("localhost", remote_port=remote_port, local_port=local_port)

    # Connect and start the DSRC thread.
    try:
        dsrc.connect()
    except Exception:
        pytest.fail("Unable to connect DSRC thread.")

    track_specialist = get_track_specialist()

    # this is an async thread
    radio.start()
    dsrc.start()

    # run for 20 seconds, then exit
    track_specialist.run()

    radio.stop()
    dsrc.stop()
