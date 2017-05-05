import sensible
import time
import os

from tests.sensor_emulator import SensorEmulator


RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591

if __name__ == '__main__':
    # Track logger
    t = time.localtime()
    log_dir = os.getcwd()
    timestamp = time.strftime('%m-%d-%Y_%H%M', t)
    p = open(os.path.join('logs', "trackLog_" + timestamp + ".csv"), 'wb')

    bsm_port = 24601
    dsrc_recv_port = 4200  # from radio
    #radar_recv_port = 4201
    dsrc_send_port = 6667  # internal
    #radar_send_port = 6668
    run_for = 25  # seconds
    freq = 5  # run at 5 Hz
    #sensor_ports = [dsrc_send_port, radar_send_port]
    sensor_ports = [dsrc_send_port]
    #topic_filters = ["DSRC", "Radar"]
    topic_filters = ["DSRC"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}

    ts = sensible.track_specialist.TrackSpecialist(sensors, bsm_port, run_for, p, frequency=freq, verbose=True)

    # radar_sender = SensorEmulator(port=radar_recv_port, pub_freq=20,
    #                               file_names=["tests/data/SW-42-SW-40/AV_Track_ID_26_GPS_track_2.csv"],
    #                               delim='\n', loop=False, delay=1, start=7, name="Radar")

    # dsrc_sender = SensorEmulator(port=dsrc_recv_port, pub_freq=20,
    #                               file_names=["tests/data/SW-42-SW-40/suilog_1492107906.txt"],
    #                               delim='CSM Tx...', loop=False, delay=1, start=193, name="DSRC")

    dsrc_recv = sensible.DSRC("localhost", remote_port=dsrc_recv_port, local_port=dsrc_send_port)
    # radar_recv = sensible.Radar("localhost", remote_port=radar_recv_port, local_port=radar_send_port,
    #                            radar_lat=RADAR_LAT, radar_lon=RADAR_LON, lane=4)   # lane 2 right turn

    # Connect and start the DSRC thread.
    try:
        dsrc_recv.connect()
        #radar_recv.connect()
    except Exception:
        print("Unable to connect DSRC and Radar sensor listeners")
        exit(1)

    dsrc_recv.start()
    #dsrc_sender.start()
    #radar_sender.start()
    #radar_recv.start()

    ts.run()

    dsrc_recv.stop()
    #dsrc_sender.stop()
    #radar_sender.stop()
    #radar_recv.stop()

