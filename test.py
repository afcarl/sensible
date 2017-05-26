import sensible
import time
import os
import sys

from tests.radar_emulator import RadarEmulator
from tests.sensor_emulator import SensorEmulator

RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591

if __name__ == '__main__':
    run_for = 60

    bsm_port = 24601

    # radar_com_port = 'COM3'
    # radar_baudrate = 115200
    radar_method = "Tracking"
    radar_orientation = 3.62  # degrees
    radar_recv_port = 4203
    dsrc_recv_port = 4200
    dsrc_send_port = 6667
    radar_send_port = 6668
    freq = 5  # run at 5 Hz
    sensor_ports = [dsrc_send_port, radar_send_port]
    topic_filters = ["DSRC", "Radar"]
    # sensor_ports = [radar_send_port]
    # topic_filters = ["Radar"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}

    # loggers
    sensible.ops.initialize_logs()

    ts = sensible.TrackSpecialist(sensors, bsm_port, run_for, sensible.ops.track_logger, association_threshold=150,
                                  n_scan=1, frequency=freq, verbose=True)

    dsrc_recv = sensible.DSRC()
    dsrc_thread = sensible.SocketThread(sensor=dsrc_recv, ip_address="localhost", port=dsrc_recv_port, msg_len=300,
                                        name="DSRCThread")

    radar_recv = sensible.Radar(mode="Tracking", lane=4, radar_lat=RADAR_LAT, radar_lon=RADAR_LON,
                                orientation=radar_orientation, verbose=False, record_csv=False)

    # 6
    radar_sender = RadarEmulator(radar=radar_recv, pub_freq=20,
                                 fname="tests/data/SW-42-SW-40/radar_log_20170502.csv", delay=6)

    dsrc_sender = SensorEmulator(port=dsrc_recv_port, pub_freq=40,
                                 file_names=["tests/data/SW-42-SW-40/NaviGator_test1-05-02.txt",
                                             "tests/data/SW-42-SW-40/dsrc_truck_1_20170502_shortened.txt"],
                                 delim='<START>', loop=False, delay=0, start=0, name="DSRC")

    # dsrc_sender = SensorEmulator(port=dsrc_recv_port, pub_freq=20,
    #                              file_names=["tests/data/SW-42-SW-40/NaviGator_test1-05-02-shortened-for-radar.txt"],
    #                              delim='<START>', loop=False, delay=3.5, start=0, name="DSRC")

    radar_synchronizer = sensible.Synchronizer(publish_freq=5, queue=radar_recv.queue, port=radar_send_port,
                                               topic=radar_recv.topic(), verbose=False, name="RadarSynchronizer")

    dsrc_synchronizer = sensible.Synchronizer(publish_freq=5, queue=dsrc_recv.queue, port=dsrc_send_port,
                                              topic=dsrc_recv.topic(), verbose=False, name="DSRCSynchronizer")

    radar_synchronizer.start()
    dsrc_synchronizer.start()
    radar_sender.start()
    dsrc_sender.start()
    dsrc_thread.start()

    ts.run()

    radar_synchronizer.stop()
    dsrc_synchronizer.stop()
    radar_sender.stop()
    dsrc_sender.stop()
    dsrc_thread.stop()

    sensible.ops.close_logs()

