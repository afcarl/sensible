import pandas as pd
import time
import os

from sensible.tracking.track_specialist import TrackSpecialist
from sensible.sensors.radar import Radar
from sensible.sensors.synchronizer import Synchronizer
from tests.radar_emulator import RadarEmulator

RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591


def get_track_specialist(tmpdir, bsm_port=6669, run_for=20.0, frequency=5):
    """Return a standard TrackSpecialist object for testing."""
    sensor_ports = [4200]
    topic_filters = ["Radar"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}
    p = tmpdir.mkdir("logs").join("test.txt")
    return TrackSpecialist(sensors, bsm_port, run_for, p, frequency=frequency, verbose=True)


def test_radar_track(tmpdir):
    """
    Test that the radar KF tracks a radar track correctly
    :return:
    """
    local_port = 4200

    radar_parser = Radar(mode="Tracking", lane=4, radar_lat=RADAR_LAT, radar_lon=RADAR_LON)
    radar = RadarEmulator(radar=radar_parser, pub_freq=20, fname="data\SW-42-SW-40\LiveExport_20170502_171908.csv")
    synchronizer = Synchronizer(publish_freq=5, queue=radar_parser.queue, port=local_port,
                                topic=radar_parser.topic(), verbose=True, name="RadarSynchronizer")
    synchronizer.start()
    radar.start()

    track_specialist = get_track_specialist(tmpdir, run_for=15)
    # run for 20 seconds, then exit
    track_specialist.run()

    radar.stop()
    synchronizer.stop()
    print("msgs: {}".format(radar_parser.count))
