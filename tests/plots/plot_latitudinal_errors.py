#import matplotlib
#matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import sensible.util.ops as ops
import utm
import os

N_TRACKS = 7
RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
# compute UTM coordinates of the radar
x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)
data_dir1 = '..\data\SW-16-SW-13'
data_dir2 = 'new_data'

if __name__ == '__main__':
    #radar_x = ops.load_pkl(os.path.join(data_dir, 'radar_x.pkl'))
    gps_x1 = ops.load_pkl(os.path.join(data_dir1, 'gps_x.pkl'))
    suitcase_x1 = ops.load_pkl(os.path.join(data_dir1, 'suitcase_gps_x.pkl'))

    #radar_speed = ops.load_pkl(os.path.join(data_dir, 'radar_speed.pkl'))
    suitcase_heading1 = ops.load_pkl(os.path.join(data_dir1, 'suitcase_heading.pkl'))
    gps_heading1 = ops.load_pkl(os.path.join(data_dir1, 'gps_heading.pkl'))

    #radar_x = ops.load_pkl(os.path.join(data_dir, 'radar_x.pkl'))
    gps_x2 = ops.load_pkl(os.path.join(data_dir2, 'gps_x.pkl'))
    suitcase_x2 = ops.load_pkl(os.path.join(data_dir2, 'suitcase_gps_x.pkl'))

    #radar_speed = ops.load_pkl(os.path.join(data_dir, 'radar_speed.pkl'))
    suitcase_heading2 = ops.load_pkl(os.path.join(data_dir2, 'suitcase_heading.pkl'))
    gps_heading2 = ops.load_pkl(os.path.join(data_dir2, 'gps_heading.pkl'))

    errs_x = []
    errs_heading = []
    errs_speed = []
    # errs_hp_radar_lat_all = []
    # errs_lp_radar_lat_all = []
    # errs_hp_radar_lat_incremental_meters = [[] for _ in range(5)]
    # errs_hp_radar_lat_incremental_feet = [[] for _ in range(5)]
    
    track_2_start = 27
    track_7_start = 10
    for ii in range(N_TRACKS):
        if ii == 2:
            start = track_2_start
        elif ii == 6:
            start = track_7_start
        else:
            start = 0

        # for j in range(len(radar_x[ii])):
        #     radar_x[ii][j] -= x
        #     gps_x[ii][j] -= x
        #     suitcase_x[ii][j] -= x

        errs_x_start_idx = len(errs_x)
        idx_x = 0

        if ii < 7:
            # Suitcase vs HP GPS easting error
            for x1, x2 in zip(suitcase_x2[ii], gps_x2[ii]):
                if idx_x < start:
                    idx_x += 1
                    continue

                errs_x.append(x2 - x1)
                idx_x += 1

            idx_x = 0
            for x1, x2 in zip(suitcase_heading2[ii], gps_heading2[ii]):
                if idx_x < start:
                    idx_x += 1
                    continue

                errs_heading.append(x2 - x1)
                idx_x += 1

            # idx_x = 0
            # for x1, x2 in zip(suitcase_speed[ii], gps_speed[ii]):
            #     if idx_x < start:
            #         idx_x += 1
            #         continue
            #
            #     errs_speed.append(x2 - x1)
            #     idx_x += 1
        else:
            idx_x = 0
            # Suitcase vs HP GPS easting error
            for x1, x2 in zip(suitcase_x1[0], gps_x1[0]):
                if idx_x < start:
                    idx_x += 1
                    continue

                errs_x.append(x2 - x1)
                idx_x += 1

            idx_x = 0
            for x1, x2 in zip(suitcase_heading1[0], gps_heading1[0]):
                if idx_x < start:
                    idx_x += 1
                    continue

                z = x2 - x1
                if z > 30:
                    continue
                errs_heading.append(z)
                idx_x += 1

        # compare range of HP GPS and radar for all tracks
        # idx = 0
        # for x1, x2 in zip(gps_x[ii], radar_x[ii]):
        #     errs_hp_radar_lat_all.append(x1 - x2)
        #     idx += 1
        #
        # # compare range of LP GPS and radar for all tracks
        # idx = 0
        # for x1, x2 in zip(suitcase_x[ii], radar_x[ii]):
        #     if idx < start:
        #         idx += 1
        #         continue
        #     errs_lp_radar_lat_all.append(x1 - x2)
        #     idx += 1
        #
        # idx = 0
        # for x1, x2 in zip(gps_x[ii], radar_x[ii]):
        #     yy = radar_y[ii][idx] - y
        #
        #     # 0 -> 100 m
        #     if 0 <= yy < 50:
        #         errs_hp_radar_lat_incremental_meters[0].append(x1 - x2)
        #     elif 50 < yy <= 100:
        #         errs_hp_radar_lat_incremental_meters[1].append(x1 - x2)
        #     elif 100 < yy <= 150:
        #         errs_hp_radar_lat_incremental_meters[2].append(x1 - x2)
        #     elif 150 < yy <= 200:
        #         errs_hp_radar_lat_incremental_meters[3].append(x1 - x2)
        #     elif 200 < yy <= 300:
        #         errs_hp_radar_lat_incremental_meters[4].append(x1 - x2)
        #     idx += 1
        #
        # idx = 0
        # for x1, x2 in zip(gps_x[ii], radar_x[ii]):
        #     yy = radar_y[ii][idx] - y
        #
        #     # 0 -> 100 ft
        #     if 0 <= yy < 30.48:
        #         errs_hp_radar_lat_incremental_feet[0].append(x1 - x2)
        #     elif 30.48 < yy <= 60.96:
        #         errs_hp_radar_lat_incremental_feet[1].append(x1 - x2)
        #     elif 60.96 < yy <= 91.44:
        #         errs_hp_radar_lat_incremental_feet[2].append(x1 - x2)
        #     elif 91.44 < yy <= 121.92:
        #         errs_hp_radar_lat_incremental_feet[3].append(x1 - x2)
        #     elif 121.92 < yy <= 152.4:
        #         errs_hp_radar_lat_incremental_feet[4].append(x1 - x2)
        #     idx += 1

        #data_dir = ''
        if ii < 7:
            # PLACE PER-TRACK PLOTTING HERE
            plt.scatter(range(len(suitcase_x2[ii][start:])), suitcase_x2[ii][start:], c='r', label='WAAS-GPS')
            plt.scatter(range(len(gps_x2[ii][start:])), gps_x2[ii][start:], c='b', label='HP-GPS')
            plt.title('Error between GPS/IMU and WAAS-GPS UTM Easting estimate\nRun %d' % (ii + 1))
            plt.legend()
            plt.ylabel('meters')
            plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
            plt.grid(True)
            fig = plt.gcf()
            fig.set_size_inches(8, 6)
            fig.savefig(os.path.join('imgs/hp-vs-lp-gps-lat-errors-track-' + str(ii + 1) + '.png'), dpi=100)
            plt.close()

            # histogram
            fig, axarr = plt.subplots(2)
            axarr[0].hist(errs_x[errs_x_start_idx: errs_x_start_idx + len(gps_x2[ii]) - start], bins=15)
            axarr[0].set_title(
                'Error between GPS/IMU and WAAS-GPS UTM Easting estimates for Run %d' % (ii + 1))
            axarr[0].grid(True)
            axarr[1].scatter(range(len(gps_x2[ii][start:])),
                             errs_x[errs_x_start_idx: errs_x_start_idx + len(gps_x2[ii]) - start])
            axarr[1].set_xlabel(r'$\bigtriangleup$ t = 100 ms')
            fig.set_size_inches(8, 8)
            plt.grid(True)
            fig.savefig(os.path.join('imgs/hp-vs-lp-gps-lat-errors-hist-track-' + str(ii + 1) + '.png'),
                        dpi=100)
            plt.close()
        else:
            # PLACE PER-TRACK PLOTTING HERE
            plt.scatter(range(len(suitcase_x1[0][start:])), suitcase_x1[0][start:], c='r', label='WAAS-GPS')
            plt.scatter(range(len(gps_x1[0][start:])), gps_x1[0][start:], c='b', label='HP-GPS')
            plt.title('Error between GPS/IMU and WAAS-GPS UTM Easting estimate\nRun %d' % (0 + 1))
            plt.legend()
            plt.ylabel('meters')
            plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
            plt.grid(True)
            fig = plt.gcf()
            fig.set_size_inches(8, 6)
            fig.savefig(os.path.join(data_dir1, 'imgs/hp-vs-lp-gps-lat-errors-track-' + str(0 + 1) + '.png'),
                        dpi=100)
            plt.close()

            # histogram
            fig, axarr = plt.subplots(2)
            axarr[0].hist(errs_x[errs_x_start_idx: errs_x_start_idx + len(gps_x1[0]) - start], bins=15)
            axarr[0].set_title('UTM Easting error histogram - Westbound')
            axarr[0].grid(True)
            axarr[0].set_xlabel('meters')
            axarr[1].scatter(range(len(gps_x1[0][start:])),
                             errs_x[errs_x_start_idx: errs_x_start_idx + len(gps_x1[0]) - start])
            axarr[1].set_xlabel(r'time, $\bigtriangleup$ t = 0.1 s')
            axarr[1].set_ylabel('meters')
            fig.set_size_inches(8, 8)
            plt.grid(True)
            fig.savefig(
                os.path.join(data_dir1, 'imgs/hp-vs-lp-gps-lat-errors-hist-track-' + str(0 + 1) + '.png'),
                dpi=100)
            plt.close()

        # PLACE PER-TRACK PLOTTING HERE
        # plt.scatter(range(len(suitcase_x[ii][start:])), suitcase_x[ii][start:], c='r', label='WAAS-GPS')
        # plt.scatter(range(len(gps_x[ii][start:])), gps_x[ii][start:], c='b', label='GPS/IMU')
        # plt.title('GPS/IMU and WAAS GPS horizontal pos estimation errors\nRun %d' % (ii+1))
        # plt.legend()
        # plt.ylabel('meters')
        # plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
        # plt.grid(True)
        # fig = plt.gcf()
        # fig.set_size_inches(8, 6)
        # fig.savefig(os.path.join(data_dir, 'imgs/hp-vs-lp-gps-lat-errors-track-' + str(ii+1) + '.png'), dpi=100)
        # plt.close()
        #
        # # histogram
        # fig, axarr = plt.subplots(2)
        # axarr[0].hist(errs_x[errs_x_start_idx: errs_x_start_idx + len(gps_x[ii]) - start], bins=15)
        # axarr[0].set_title('GPS/IMU and WAAS GPS horizontal pos estimation errors\nRun %d' % (ii + 1))
        # axarr[0].grid(True)
        # axarr[1].scatter(range(len(gps_x[ii][start:])), errs_x[errs_x_start_idx: errs_x_start_idx + len(gps_x[ii]) - start])
        # axarr[1].set_xlabel(r'$\bigtriangleup$ t = 100 ms')
        # fig.set_size_inches(8, 8)
        # plt.grid(True)
        # fig.savefig(os.path.join(data_dir, 'imgs/hp-vs-lp-gps-lat-errors-hist-track-' + str(ii+1) + '.png'), dpi=100)
        # plt.close()

    # fig, axarr = plt.subplots(2)
    # axarr[0].hist(errs_x, bins=15)
    # axarr[0].set_title('GPS/IMU and WAAS GPS horizontal pos estimation errors')
    # axarr[0].grid(True)
    # axarr[1].hist(errs_x_abs, bins=15)
    # axarr[1].set_title('Absolute error')
    # axarr[1].set_xlabel('meters')
    # fig.set_size_inches(8, 8)
    # plt.grid(True)
    # fig.savefig(os.path.join(data_dir, 'imgs/hp-vs-lp-gps-lat-errors.png'), dpi=100)
    # plt.close()

    ops.dump(errs_x, os.path.join(data_dir1, 'suitcase_gps_x_errors.pkl'))
    ops.dump(errs_heading, os.path.join(data_dir1, 'suitcase_gps_heading_errors.pkl'))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_x, bins=10)
    ax.set_xlabel('meters')
    ax.set_ylabel('frequency')
    ax.set_title('UTM Easting Ground Truth measurement error histogram')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig(os.path.join('imgs/DIVANET/SW-16-hp-vs-lp-lat-errors.png'), dpi=100)
    plt.close()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_heading, bins=10)
    ax.set_xlabel('degrees')
    ax.set_ylabel('frequency')
    ax.set_title('Vehicle heading Ground Truth error histogram')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig(os.path.join('imgs/DIVANET/SW-16-hp-vs-lp-yaw-errors.png'), dpi=100)
    plt.close()

    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    # ax.hist(errs_speed, bins=15)
    # ax.set_xlabel('speed m/s')
    # ax.set_title('GPS/IMU and radar speed estimation errors')
    # fig.set_size_inches(8, 6)
    # plt.grid(True)
    # fig.savefig(os.path.join(data_dir, 'imgs/hp-vs-lp-speed-errors.png'), dpi=100)
    # plt.close()

    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    # ax.hist(errs_hp_radar_lat_all, bins=25)
    # ax.set_xlabel('meters')
    # ax.set_title('GPS/IMU and radar horizontal pos estimation errors')
    # fig.set_size_inches(8, 6)
    # plt.grid(True)
    # fig.savefig('imgs/hp-vs-radar-lat-error.png', dpi=100)
    # plt.close()
    #
    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    # ax.hist(errs_lp_radar_lat_all, bins=25)
    # ax.set_xlabel('meters')
    # ax.set_title('Radar and WAAS GPS horizontal pos estimation errors')
    # fig.set_size_inches(8, 6)
    # plt.grid(True)
    # fig.savefig('imgs/lp-vs-radar-lat-error.png', dpi=100)
    # plt.close()
    #
    # fig, axarr = plt.subplots(5, sharex=True)
    # titles = ["Error between GPS/IMU and radar horizontal pos estimates\n0 - 50 m", "50 - 100 m", "100 - 150 m", "150 - 200 m",
    #           "200 - 300 m"]
    # for i in range(5):
    #     axarr[i].hist(errs_hp_radar_lat_incremental_meters[i], bins=15)
    #     axarr[i].set_title(titles[i])
    #     axarr[i].grid(True)
    # axarr[-1].set_xlabel('meters')
    # fig.set_size_inches(8, 8)
    # fig.savefig('imgs/hp-vs-radar-lat-incremental-meters.png', dpi=100)
    # plt.close()
    #
    # fig, axarr = plt.subplots(5, sharex=True)
    # titles = ["Error between GPS/IMU and radar horizontal pos estimates\n0 - 100 ft", "100 - 200 ft", "200 - 300 ft",
    #           "300 - 400 ft", "400 - 500 ft"]
    # for i in range(5):
    #     axarr[i].hist(errs_hp_radar_lat_incremental_feet[i], bins=15)
    #     axarr[i].set_title(titles[i])
    #     axarr[i].grid(True)
    # axarr[-1].set_xlabel('meters')
    # fig.set_size_inches(8, 8)
    # fig.savefig('imgs/hp-vs-radar-lat-incremental-feet.png', dpi=100)
    # plt.close()

    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    # colors = ['r', 'g', 'b', 'y', 'm', 'c']
    # start = 0
    # for i in range(N_TRACKS):
    #     for j in range(len(radar_y[i])):
    #         plt.scatter(speed[start + j], errs_hp_radar_lat_all[start + j], c=colors[i])
    #     start += len(radar_y[i])
    # ax.set_xlabel('m/s')
    # ax.set_ylabel('meters')
    # ax.set_title('Radar speed vs lat error')
    # fig.set_size_inches(8, 6)
    # plt.grid(True)
    # fig.savefig('imgs/radar-speed-lat-error.png', dpi=100)