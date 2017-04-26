import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import sensible.util.ops as ops
import utm
import scipy

N_TRACKS = 6
RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
# compute UTM coordinates of the radar
x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

if __name__ == '__main__':
    radar_y = ops.load_pkl('radar_y.pkl')
    gps_y = ops.load_pkl('gps_y.pkl')
    suitcase_y = ops.load_pkl('suitcase_gps_y.pkl')

    errs_y = []
    errs_y_abs = []
    errs_hp_radar_range_all = []
    errs_lp_radar_range_all = []
    errs_hp_radar_range_incremental_meters = [[] for _ in range(5)]
    errs_hp_radar_range_incremental_feet = [[] for _ in range(5)]

    track_2_start = 27
    track_7_start = 10
    for ii in range(N_TRACKS):

        for j in range(len(radar_y[ii])):
            radar_y[ii][j] -= y
            gps_y[ii][j] -= y
            suitcase_y[ii][j] -= y

        if ii == 1:
            start = track_2_start
        elif ii == 5:
            start = track_7_start
        else:
            start = 0

        idx_y = 0
        # Suitcase vs HP GPS northing error
        for y1, y2 in zip(suitcase_y[ii], gps_y[ii]):
            if idx_y < start:
                idx_y += 1
                continue

            errs_y.append(y2 - y1)
            errs_y_abs.append(abs(y2 - y1))
            idx_y += 1

        # compare range of HP GPS and radar for all tracks
        for y1, y2 in zip(gps_y[ii], radar_y[ii]):
            #errs_hp_radar_range_all.append((y1 - 3.6576) - y2)
            errs_hp_radar_range_all.append(y1 - y2)

        # compare range of LP GPS and radar for all tracks
        idx = 0
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

        # PLACE PER-TRACK PLOTTING HERE
        plt.scatter(range(len(suitcase_y[ii][start:])), suitcase_y[ii][start:], c='r', label='LP-GPS')
        plt.scatter(range(len(gps_y[ii][start:])), gps_y[ii][start:], c='b', label='HP-GPS')
        plt.title('High- vs low-precision GPS range\ntrack %d' % (ii+1))
        plt.legend()
        plt.ylabel('meters')
        plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
        plt.grid(True)
        fig = plt.gcf()
        fig.set_size_inches(8, 6)
        fig.savefig('imgs/hp-vs-lp-gps-range-errors-track-' + str(ii+1) + '.png', dpi=100)
        plt.clf()

    fig, axarr = plt.subplots(2)
    axarr[0].hist(errs_y, bins=15)
    axarr[0].set_title('Error between low- and high-precision GPS range')
    axarr[1].hist(errs_y_abs, bins=15)
    axarr[1].set_title('Absolute error')
    axarr[1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    plt.grid(True)
    fig.savefig('imgs/hp-vs-lp-gps-range-errors.png', dpi=100)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_hp_radar_range_all, bins=25)
    ax.set_xlabel('meters')
    ax.set_title('Error between high-precision GPS and radar range')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig('imgs/hp-vs-radar-range-error.png', dpi=100)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_lp_radar_range_all, bins=25)
    ax.set_xlabel('meters')
    ax.set_title('Error between low-precision GPS and radar range')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig('imgs/lp-vs-radar-range-error.png', dpi=100)

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between high-precision GPS and radar range\n0 - 50 m", "50 - 100 m", "100 - 150 m", "150 - 200 m", "200 - 300 m"]
    for i in range(5):
        axarr[i].hist(errs_hp_radar_range_incremental_meters[i], bins=15)
        axarr[i].set_title(titles[i])
    axarr[-1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    plt.grid(True)
    fig.savefig('imgs/hp-vs-radar-range-incremental-meters.png', dpi=100)

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between high-precision GPS and radar range\n0 - 100 ft", "100 - 200 ft", "200 - 300 ft",
              "300 - 400 ft", "400 - 500 ft"]
    for i in range(5):
        axarr[i].hist(errs_hp_radar_range_incremental_feet[i], bins=15)
        axarr[i].set_title(titles[i])
    axarr[-1].set_xlabel('meters')
    fig.set_size_inches(8, 8)
    plt.grid(True)
    fig.savefig('imgs/hp-vs-radar-range-incremental-feet.png', dpi=100)