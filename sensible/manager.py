import sensible


class Manager:
    def __init__(self, args):
        for k, v in args.items():
            setattr(self, k, v)

    def run(self):
        if self.disable_radar and self.disable_dsrc:
            raise ValueError('Unable to disable both types of sensors')

        if not self.disable_logging:
            sensible.ops.initialize_logs()

        sensor_ports = []
        topic_filters = []
        if not self.disable_radar:
            sensor_ports.append(int(self.radar_local_port))
            topic_filters.append('Radar')
        if not self.disable_dsrc:
            sensor_ports.append(int(self.dsrc_local_port))
            topic_filters.append('DSRC')

        sensors = {'sensor_ports': sensor_ports, 'topic_filters': topic_filters}

        ts = sensible.TrackSpecialist(sensors, int(self.output_port), int(self.run_for),
                                      sensible.ops.track_logger, n_scan=int(self.n_scan),
                                      frequency=int(self.track_frequency),
                                      association_threshold=int(self.association_threshold), verbose=self.v)

        if not self.disable_dsrc:
            dsrc_recv = sensible.DSRC()
            dsrc_thread = sensible.SocketThread(sensor=dsrc_recv, ip_address=self.dsrc_ip_address,
                                                port=int(self.dsrc_remote_port), msg_len=300, name='DSRCThread')
            dsrc_synchronizer = sensible.Synchronizer(publish_freq=int(self.track_frequency), queue=dsrc_recv.queue,
                                                      port=int(self.dsrc_local_port),
                                                      topic=dsrc_recv.topic(), verbose=False, name='DSRCSynchronizer')
            dsrc_synchronizer.start()
            dsrc_thread.start()

        if not self.disable_radar:
            radar_recv = sensible.Radar(mode=self.radar_mode, lane=int(self.radar_lane),
                                        radar_lat=float(self.radar_lat), radar_lon=float(self.radar_lon),
                                        record_csv=self.record_csv, verbose=False)

            radar_thread = sensible.SerialThread(radar_recv, self.radar_com_port, int(self.radar_baudrate),
                                                 name='RadarThread')

            radar_synchronizer = sensible.Synchronizer(publish_freq=int(self.track_frequency),
                                                       queue=radar_recv.queue,
                                                       port=int(self.radar_local_port),
                                                       topic=radar_recv.topic(), verbose=False,
                                                       name='RadarSynchronizer')

            radar_synchronizer.start()
            radar_thread.start()

        sensible.ops.show("  [Sensible] Starting app...\n", True)

        ts.run()

        if not self.disable_dsrc:
            dsrc_synchronizer.stop()
            dsrc_thread.stop()

        if not self.disable_radar:
            radar_synchronizer.stop()
            radar_thread.stop()

        sensible.ops.show("  [Sensible] Shutting down app...\n", True)
        sensible.ops.close_logs()
