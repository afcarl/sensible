"""
Test the Kalman Filter with a full trajectory by simulating a radio
sending the messages in real time (20 Hz)
"""
import pytest
import time
import os

from tests.sensor_emulator import SensorEmulator
import sensible

dsrc_recv_port = 4200
internal_dsrc_port = 6666


def get_track_specialist(tmpdir, bsm_port=6667, run_for=20.0, frequency=5):
    """Return a standard TrackSpecialist object for testing."""
    sensor_ports = [internal_dsrc_port]
    topic_filters = ["DSRC"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}
    #p = tmpdir.mkdir("logs").join("test.csv")
    #Track logger
    # t = time.localtime()
    # log_dir = os.getcwd()
    # timestamp = time.strftime('%m-%d-%Y_%H%M', t)
    # p = open(os.path.join(log_dir, '..', 'logs', "trackLog_" + timestamp + ".csv"), 'wb')
    return sensible.TrackSpecialist(sensors, bsm_port, run_for, sensible.ops.track_logger, n_scan=1, frequency=frequency, verbose=True)


def test_trajectory(tmpdir):
    dsrc_sender = SensorEmulator(port=dsrc_recv_port, pub_freq=20,
                           #file_name="data/01-27-17-solarpark/GPS/Solar_UrbanNavi012717/suilog_1485534929.txt",
                           file_names=["data/SW-42-SW-40/NaviGator_test1-05-02.txt"],
                           delim="<START>", loop=False, delay=0)

    dsrc_recv = sensible.DSRC()
    dsrc_thread = sensible.SocketThread(sensor=dsrc_recv, ip_address="localhost", port=dsrc_recv_port, msg_len=300,
                                        name="DSRCThread")

    dsrc_synchronizer = sensible.Synchronizer(publish_freq=5, queue=dsrc_recv.queue, port=internal_dsrc_port,
                                              topic=dsrc_recv.topic(), verbose=False, name="DSRCSynchronizer")

    sensible.ops.initialize_logs()

    ts = get_track_specialist(tmpdir)

    dsrc_synchronizer.start()
    dsrc_sender.start()
    dsrc_thread.start()

    ts.run()

    dsrc_synchronizer.stop()
    dsrc_sender.stop()
    dsrc_thread.stop()


# def test_2_lane_tracking(tmpdir):
#     radio = SensorEmulator(port=4200, pub_freq=40,
#                            file_names=["data/11-17-16-solarpark/GPS/Solar_Suitcase111716/straight-lane-csmlog_1479402503.txt",
#                                        "data/01-27-17-solarpark/GPS/Solar_UrbanNavi012717/suilog_1485534929.txt"],
#                            delim="CSM Tx...", loop=False, delay=2)
#
#     remote_port = 4200
#     local_port = 6666
#     dsrc = DSRC("localhost", remote_port=remote_port, local_port=local_port)
#
#     # Connect and start the DSRC thread.
#     try:
#         dsrc.connect()
#     except Exception:
#         pytest.fail("Unable to connect DSRC thread.")
#
#     track_specialist = get_track_specialist(tmpdir)
#
#     # this is an async thread
#     dsrc.start()
#     radio.start()
#
#     # run for 20 seconds, then exit
#     track_specialist.run()
#
#     radio.stop()
#     dsrc.stop()
