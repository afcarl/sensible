import sensible
import time
import os
import sys

RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591

if __name__ == '__main__':
    run_for = int(sys.argv[1])  # seconds

    # Track logger
    t = time.localtime()
    log_dir = os.getcwd()
    timestamp = time.strftime('%m-%d-%Y_%H%M', t)
    p = open(os.path.join('logs', "trackLog_" + timestamp + ".csv"), 'wb')

    bsm_port = 24601
    dsrc_recv_port = 4200

    radar_com_port = 'COM3'
    radar_baudrate = 115200
    radar_method = "Tracking"

    dsrc_send_port = 6667
    radar_send_port = 6668
    freq = 5  # run at 5 Hz
    #sensor_ports = [dsrc_send_port, radar_send_port]
    #topic_filters = ["DSRC", "Radar"]
    sensor_ports = [radar_send_port]
    topic_filters = ["RadarSerial"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}

    ts = sensible.track_specialist.TrackSpecialist(sensors, bsm_port, run_for, p, frequency=freq, verbose=True)

    #dsrc_recv = sensible.DSRC("localhost", remote_port=dsrc_recv_port, local_port=dsrc_send_port)

    radar_recv = sensible.RadarSerial(radar_com_port, radar_baudrate,
                                      radar_lat=RADAR_LAT, radar_lon=RADAR_LON, mode=radar_method,
                                      lane=4, verbose=True)  # lane 2 right turn

    radar_synch = sensible.RadarSynchronizer(queue=radar_recv.queue, port=radar_send_port,
                                             topic=sensible.RadarSerial.topic(),
                                             verbose=True)

    # Connect and start the DSRC thread.
    # try:
    #     dsrc_recv.connect()
    # except Exception:
    #     print("Unable to connect DSRC and Radar sensor listeners")
    #     exit(1)

    radar_synch.start()
    #dsrc_recv.start()
    radar_recv.start()

    ts.run()

    #dsrc_recv.stop()
    radar_synch.stop()
    radar_recv.stop()

    print('radar_recv msgs: {}'.format(radar_recv.msg_count))

