import matplotlib.pyplot as plt
import sensible.util.ops as ops
import utm
import numpy as np
import os

data_dir = 'new_data'
N_TRACKS = 6
RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
# compute UTM coordinates of the radar
x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

if __name__ == '__main__':
    radar_y = ops.load_pkl(os.path.join(data_dir, 'radar_y.pkl'))
    gps_y = ops.load_pkl(os.path.join(data_dir, 'gps_y.pkl'))
    suitcase_y = ops.load_pkl(os.path.join(data_dir, 'suitcase_gps_y.pkl'))
    radar_speed = ops.load_pkl(os.path.join(data_dir, 'radar_speed.pkl'))

    errs_y = []
    errs_y_abs = []
    errs_hp_radar_range_all = []
    errs_lp_radar_range_all = []
    errs_hp_radar_range_incremental_meters = [[] for _ in range(5)]
    errs_hp_radar_range_incremental_feet = [[] for _ in range(5)]
    errs_lp_radar_range_incremental_meters = [[] for _ in range(5)]
    errs_lp_radar_range_incremental_feet = [[] for _ in range(5)]
    speed = []

    track_2_start = 27
    track_7_start = 10
    for ii in range(N_TRACKS):

        for j in range(len(radar_y[ii])):
            radar_y[ii][j] -= y
            gps_y[ii][j] -= y
            suitcase_y[ii][j] -= y
            #suitcase_y[ii][j] -= 3.6576

        if ii == 1:
            start = track_2_start
        elif ii == 5:
            start = track_7_start
        else:
            start = 0

        idx_y = 0
        errs_y_start_idx = len(errs_y)

        # Suitcase vs HP GPS northing error
        for y1, y2 in zip(suitcase_y[ii], gps_y[ii]):
            if idx_y < start:
                idx_y += 1
                continue

            errs_y.append(y2 - y1)
            errs_y_abs.append(abs(y2 - y1))
            idx_y += 1

        # compare range of HP GPS and radar for all tracks
        idx = 0
        errs_hp_radar_start = len(errs_hp_radar_range_all)
        for y1, y2 in zip(gps_y[ii], radar_y[ii]):
            #errs_hp_radar_range_all.append((y1 - 3.6576) - y2)
            errs_hp_radar_range_all.append(y1 - y2)
            speed.append(radar_speed[ii][idx])
            idx += 1

        # compare range of LP GPS and radar for all tracks
        idx = 0
        errs_lp_radar_start = len(errs_lp_radar_range_all)

        for y1, y2 in zip(suitcase_y[ii], radar_y[ii]):
            if idx < start:
                idx += 1
                continue
            errs_lp_radar_range_all.append(y1 - y2)
            idx += 1

        for y1, y2 in zip(gps_y[ii], radar_y[ii]):

            # 0 -> 100 m
            if 0 <= y2 < 50:
                errs_hp_radar_range_incremental_meters[0].append(y1 - y2)
            elif 50 < y2 <= 100:
                errs_hp_radar_range_incremental_meters[1].append(y1 - y2)
            elif 100 < y2 <= 150:
                errs_hp_radar_range_incremental_meters[2].append(y1 - y2)
            elif 150 < y2 <= 200:
                errs_hp_radar_range_incremental_meters[3].append(y1 - y2)
            elif 200 < y2 <= 300:
                errs_hp_radar_range_incremental_meters[4].append(y1 - y2)

        for y1, y2 in zip(gps_y[ii], radar_y[ii]):

            # 0 -> 100 ft
            if 0 <= y2 < 30.48:
                errs_hp_radar_range_incremental_feet[0].append(y1 - y2)
            elif 30.48 < y2 <= 60.96:
                errs_hp_radar_range_incremental_feet[1].append(y1 - y2)
            elif 60.96 < y2 <= 91.44:
                errs_hp_radar_range_incremental_feet[2].append(y1 - y2)
            elif 91.44 < y2 <= 121.92:
                errs_hp_radar_range_incremental_feet[3].append(y1 - y2)
            elif 121.92 < y2 <= 152.4:
                errs_hp_radar_range_incremental_feet[4].append(y1 - y2)

        idx = 0
        for y1, y2 in zip(suitcase_y[ii], radar_y[ii]):
            if idx < start:
                idx += 1
                continue

            # 0 -> 100 m
            if 0 <= y2 < 50:
                errs_lp_radar_range_incremental_meters[0].append(y1 - y2)
            elif 50 < y2 <= 100:
                errs_lp_radar_range_incremental_meters[1].append(y1 - y2)
            elif 100 < y2 <= 150:
                errs_lp_radar_range_incremental_meters[2].append(y1 - y2)
            elif 150 < y2 <= 200:
                errs_lp_radar_range_incremental_meters[3].append(y1 - y2)
            elif 200 < y2 <= 300:
                errs_lp_radar_range_incremental_meters[4].append(y1 - y2)
            idx += 1

        idx = 0
        for y1, y2 in zip(suitcase_y[ii], radar_y[ii]):
            if idx < start:
                idx += 1
                continue

            # 0 -> 100 ft
            if 0 <= y2 < 30.48:
                errs_lp_radar_range_incremental_feet[0].append(y1 - y2)
            elif 30.48 < y2 <= 60.96:
                errs_lp_radar_range_incremental_feet[1].append(y1 - y2)
            elif 60.96 < y2 <= 91.44:
                errs_lp_radar_range_incremental_feet[2].append(y1 - y2)
            elif 91.44 < y2 <= 121.92:
                errs_lp_radar_range_incremental_feet[3].append(y1 - y2)
            elif 121.92 < y2 <= 152.4:
                errs_lp_radar_range_incremental_feet[4].append(y1 - y2)
            idx += 1

        # PLACE PER-TRACK PLOTTING HERE
        plt.scatter(range(len(suitcase_y[ii][start:])), suitcase_y[ii][start:], c='r', label='WAAS-GPS')
        plt.scatter(range(len(gps_y[ii][start:])), gps_y[ii][start:], c='b', label='HP-GPS')
        plt.title('Error between GPS/IMU and WAAS-GPS UTM Northing estimate\nRun %d' % (ii+1))
        plt.legend()
        plt.ylabel('meters')
        plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
        plt.grid(True)
        fig = plt.gcf()
        fig.set_size_inches(8, 6)
        fig.savefig('imgs/hp-vs-lp-gps-range-errors-track-' + str(ii+1) + '.png', dpi=100)
        plt.close()

        # histogram
        fig, axarr = plt.subplots(2)
        axarr[0].hist(errs_y[errs_y_start_idx: errs_y_start_idx + len(gps_y[ii]) - start], bins=15)
        axarr[0].set_title('Error between GPS/IMU and WAAS-GPS UTM Northing estimates for run %d' % (ii + 1))
        axarr[0].grid(True)
        axarr[1].scatter(range(len(gps_y[ii][start:])), errs_y[errs_y_start_idx: errs_y_start_idx + len(gps_y[ii]) - start])
        axarr[1].set_xlabel(r'$\bigtriangleup$ t = 100 ms')
        fig.set_size_inches(8, 8)
        plt.grid(True)
        fig.savefig('imgs/hp-vs-lp-gps-range-errors-hist-track-' + str(ii+1) + '.png', dpi=100)
        plt.close()

        # histogram
        fig, axarr = plt.subplots(2)
        axarr[0].hist(errs_lp_radar_range_all[errs_lp_radar_start: errs_lp_radar_start + len(suitcase_y[ii]) - start], bins=15)
        axarr[0].set_title('Error between WAAS-GPS and Radar UTM Northing estimates for run %d' % (ii + 1))
        axarr[0].grid(True)
        axarr[1].scatter(range(len(suitcase_y[ii][start:])),
                         errs_lp_radar_range_all[errs_lp_radar_start: errs_lp_radar_start + len(suitcase_y[ii]) - start])
        axarr[1].set_xlabel(r'$\bigtriangleup$ t = 100 ms')
        fig.set_size_inches(8, 8)
        plt.grid(True)
        fig.savefig('imgs/lp-vs-radar-range-errors-hist-track-' + str(ii + 1) + '.png', dpi=100)
        plt.close()

        # histogram
        fig, axarr = plt.subplots(2)
        axarr[0].hist(errs_hp_radar_range_all[errs_hp_radar_start: errs_hp_radar_start + len(gps_y[ii]) - start],
                      bins=15)
        axarr[0].set_title('Error between GPS/IMU and radar UTM Northing estimates for run %d' % (ii + 1))
        axarr[0].grid(True)
        axarr[1].scatter(range(len(gps_y[ii][start:])),
                         errs_hp_radar_range_all[
                         errs_hp_radar_start: errs_hp_radar_start + len(gps_y[ii]) - start])
        axarr[1].set_xlabel(r'$\bigtriangleup$ t = 100 ms')
        fig.set_size_inches(8, 8)
        plt.grid(True)
        fig.savefig('imgs/hp-vs-radar-range-errors-hist-track-' + str(ii + 1) + '.png', dpi=100)
        plt.close()

        # range errors histogram of radar-vs-HP GPS and low-prec GPS-vs-HP GPS
        plt.scatter(range(len(gps_y[ii][start:])), errs_y[errs_y_start_idx: errs_y_start_idx + len(gps_y[ii]) - start], c='r', label='WAAS-GPS')
        plt.scatter(range(len(gps_y[ii][start:])),
                         errs_hp_radar_range_all[
                         errs_hp_radar_start: errs_hp_radar_start + len(gps_y[ii]) - start], c='b', label='Radar')
        plt.title('WAAS-GPS and radar UTM Northing estimate errors compared to GPS/IMU\nRun %d' % (ii + 1))
        plt.legend()
        plt.ylabel('meters')
        plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
        plt.grid(True)
        fig = plt.gcf()
        fig.set_size_inches(8, 6)
        fig.savefig('imgs/lp-radar-vs-hp-gps-range-errors-track-' + str(ii + 1) + '.png', dpi=100)
        plt.close()

    ops.dump(errs_y, 'new_data/suitcase_gps_y_errors.pkl')

    fig, axarr = plt.subplots(2)
    axarr[0].hist(errs_y, bins=15)
    axarr[0].set_title('Error between GPS/IMU and WAAS-GPS UTM Northing estimates')
    axarr[0].grid(True)
    axarr[1].hist(errs_y_abs, bins=15)
    axarr[1].set_title('Absolute error')
    axarr[1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    plt.grid(True)
    fig.savefig('imgs/hp-vs-lp-gps-range-errors.png', dpi=100)
    plt.close()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_hp_radar_range_all, bins=25)
    ax.set_xlabel('meters')
    ax.set_title('Error between GPS/IMU and radar UTM Northing estimates')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig('imgs/hp-vs-radar-range-error.png', dpi=100)
    plt.close()

    # compute sample mean and variance
    sample_mu = np.mean(errs_hp_radar_range_all)
    sample_sigma = np.var(errs_hp_radar_range_all, ddof=1)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_lp_radar_range_all, bins=25)
    ax.set_xlabel('meters')
    ax.set_title('Error between WAAS-GPS and radar UTM Northing estimates')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig('imgs/lp-vs-radar-range-error.png', dpi=100)
    plt.close()

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between GPS/IMU and radar UTM Northing estimates\n0 - 50 m", "50 - 100 m", "100 - 150 m", "150 - 200 m", "200 - 300 m"]
    for i in range(5):
        axarr[i].hist(errs_hp_radar_range_incremental_meters[i], bins=15)
        axarr[i].set_title(titles[i])
        axarr[i].grid(True)
    axarr[-1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    fig.savefig('imgs/hp-vs-radar-range-incremental-meters.png', dpi=100)
    plt.close()

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between WAAS-GPS and radar UTM Northing estimates\n0 - 50 m", "50 - 100 m", "100 - 150 m", "150 - 200 m",
              "200 - 300 m"]
    for i in range(5):
        axarr[i].hist(errs_lp_radar_range_incremental_meters[i], bins=15)
        axarr[i].set_title(titles[i])
        axarr[i].grid(True)
    axarr[-1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    fig.savefig('imgs/lp-vs-radar-range-incremental-meters.png', dpi=100)
    plt.close()

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between WAAS-GPS and radar UTM Northing estimates\n0 - 100 ft", "100 - 200 ft", "200 - 300 ft",
              "300 - 400 ft", "400 - 500 ft"]
    for i in range(5):
        axarr[i].hist(errs_lp_radar_range_incremental_feet[i], bins=15)
        axarr[i].set_title(titles[i])
        axarr[i].grid(True)
    axarr[-1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    fig.savefig('imgs/lp-vs-radar-range-incremental-feet.png', dpi=100)
    plt.close()

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between GPS/IMU and radar UTM Northing estimates\n0 - 100 ft", "100 - 200 ft", "200 - 300 ft",
              "300 - 400 ft", "400 - 500 ft"]
    for i in range(5):
        axarr[i].hist(errs_hp_radar_range_incremental_feet[i], bins=15)
        axarr[i].set_title(titles[i])
        axarr[i].grid(True)
        #print("Variance for {} is {}".format(titles[i], np.var(errs_hp_radar_range_incremental_feet[i], axis=0, ddof=1)))
    axarr[-1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    fig.savefig('imgs/hp-vs-radar-range-incremental-feet.png', dpi=100)
    plt.close()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    colors = ['r', 'g', 'b', 'y', 'm', 'c']
    start = 0
    for i in range(N_TRACKS):
        for j in range(len(radar_y[i])):
            plt.scatter(speed[start + j], errs_hp_radar_range_all[start + j], c=colors[i])
        start += len(radar_y[i])
    ax.set_xlabel('m/s')
    ax.set_ylabel('meters')
    ax.set_title('Errors in Radar speed and UTM Northing estimates')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig('imgs/radar-speed-range-error.png', dpi=100)
    plt.close()