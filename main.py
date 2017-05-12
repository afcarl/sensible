#!/usr/bin/python
import sensible
import time
import os
import argparse


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Arguments for Sensible')

    parser.add_argument('--run-for', default=60, help='Num seconds to run application for')
    parser.add_argument('--radar-lat', default=29.6216931, help='Latitude of radar')
    parser.add_argument('--radar-lon', default=-82.3867591, help='Longitude of radar')
    parser.add_argument('--radar-com-port', default='COM3', help='Serial port for radar comms')
    parser.add_argument('--radar-baudrate', default=115200, help='Baudrate for radar serial comms')
    parser.add_argument('--radar-mode', default='Tracking', help='Options are {Tracking|Zone}')
    parser.add_argument('--radar-lane', default=4, help='Lane # to append to radar outgoing message')
    parser.add_argument('--radar-local-port', default=5200, help='Port for comms between radar and'
                                                                 ' central tracking component')
    parser.add_argument('--dsrc-ip-address', default='169.254.30.4', help='IP address for comms with DSRC radio')
    parser.add_argument('--dsrc-remote-port', default=4200, help='Port for receiving incoming radio messages')
    parser.add_argument('--dsrc-local-port', default=4202, help='Port for comms between dsrc and'
                                                                ' central tracking component')
    parser.add_argument('--track-frequency', default=5, help='Frequency (Hz) at which to run the central tracking system')
    parser.add_argument('--output-port', default=24601, help='Port on localhost to which to forward tracking info')
    parser.add_argument('--v', action='store_true', help='Verbose output')
    parser.add_argument('--disable-logging', action='store_true', help='Enable logging')
    parser.add_argument('--disable-radar', action='store_true', help='Only run with DSRC tracking')
    parser.add_argument('--disable-dsrc', action='store_true', help='Only run with radar tracking')
    parser.add_argument('--record-csv', action='store_true', help='Record all radar msgs to a .csv')

    parser.set_defaults(disable_logging=False)
    parser.set_defaults(v=False)
    parser.set_defaults(disable_radar=False)
    parser.set_defaults(disable_dsrc=False)
    parser.set_defaults(record_csv=False)

    args = vars(parser.parse_args())

    if args['disable_radar'] and args['disable_dsrc']:
        raise ValueError('Unable to disable both types of sensors')

    if not args['disable_logging']:
        sensible.ops.initialize_logs()

    sensor_ports = []
    topic_filters = []
    if not args['disable_radar']:
        sensor_ports.append(int(args['radar_local_port']))
        topic_filters.append('Radar')
    if not args['disable_dsrc']:
        sensor_ports.append(int(args['dsrc_local_port']))
        topic_filters.append('DSRC')

    sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}

    ts = sensible.TrackSpecialist(sensors, int(args['output_port']), int(args['run_for']),
                                  sensible.ops.track_logger, frequency=int(args['track_frequency']), verbose=args['v'])

    if not args['disable_dsrc']:
        dsrc_recv = sensible.DSRC()
        dsrc_thread = sensible.SocketThread(sensor=dsrc_recv, ip_address=args['dsrc_ip_address'],
                                            port=int(args['dsrc_remote_port']), msg_len=300, name='DSRCThread')
        dsrc_synchronizer = sensible.Synchronizer(publish_freq=int(args['track_frequency']), queue=dsrc_recv.queue,
                                                  port=int(args['dsrc_local_port']),
                                                  topic=dsrc_recv.topic(), verbose=False, name='DSRCSynchronizer')
        dsrc_synchronizer.start()
        dsrc_thread.start()

    if not args['disable_radar']:
        radar_recv = sensible.Radar(mode=args['radar_mode'], lane=int(args['radar_lane']),
                                    radar_lat=float(args['radar_lat']), radar_lon=float(args['radar_lon']),
                                    record_csv=args['record_csv'], verbose=False)

        radar_thread = sensible.SerialThread(radar_recv, args['radar_com_port'], int(args['radar_baudrate']),
                                             name='RadarThread')

        radar_synchronizer = sensible.Synchronizer(publish_freq=int(args['track_frequency']), queue=radar_recv.queue,
                                                   port=int(args['radar_local_port']),
                                                   topic=radar_recv.topic(), verbose=False, name='RadarSynchronizer')

        radar_synchronizer.start()
        radar_thread.start()

    sensible.ops.show("  [Sensible] Starting app...\n", True)

    ts.run()

    if not args['disable_dsrc']:
        dsrc_synchronizer.stop()
        dsrc_thread.stop()

    if not args['disable_radar']:
        radar_synchronizer.stop()
        radar_thread.stop()

    sensible.ops.show("  [Sensible] Shutting down app...\n", True)
    sensible.ops.close_logs()
