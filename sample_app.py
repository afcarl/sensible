import sensible


if __name__ == '__main__':
    # TODO: use argparse
    logdir = ""

    bsm_port = 24601
    dsrc_recv_port = 4200
    radar_recv_port = 4201
    dsrc_send_port = 6667
    radar_send_port = 6668
    run_for = 20  # seconds
    period = 0.2  # tenths of a second
    sensor_ports = [dsrc_send_port, radar_send_port]
    topic_filters = ["DSRC", "Radar"]
    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}

    ts = sensible.track_specialist.TrackSpecialist(sensors, bsm_port, run_for, period, logdir)

    dsrc_recv = sensible.DSRC("localhost", remote_port=dsrc_recv_port, local_port=dsrc_send_port)
    radar_recv = sensible.Radar("localhost", remote_port=radar_recv_port, local_port=radar_send_port)

    # Connect and start the DSRC thread.
    try:
        dsrc_recv.connect()
        radar_recv.connect()
    except Exception:
        print("Unable to connect DSRC and Radar sensor listeners")
        exit(1)

    dsrc_recv.start()
    radar_recv.start()

    ts.run()

    dsrc_recv.stop()
    radar_recv.stop()

