import matplotlib.pyplot as plt
import sensible.util.ops as ops
import utm

N_TRACKS = 6
RADAR_LAT = 29.6216931
RADAR_LON = -82.3867591
# compute UTM coordinates of the radar
x, y, zone, letter = utm.from_latlon(RADAR_LAT, RADAR_LON)

if __name__ == '__main__':
    radar_speed = ops.load_pkl('radar_speed.pkl')
    suitcase_speed = ops.load_pkl('suitcase_speed.pkl')
    suitcase_heading = ops.load_pkl('suitcase_heading.pkl')
    radar_y = ops.load_pkl('radar_y.pkl')

    errs_lp_radar_speed_all = []
    errs_lp_radar_speed_incremental_meters = [[] for _ in range(5)]
    errs_lp_radar_speed_incremental_feet = [[] for _ in range(5)]

    track_2_start = 27
    track_7_start = 10
    ylims = [(-14.5, -11), (-14, -6), (-10, -7), (-10, -7), (-17.5, -13.5), (-20, -2)]
    for ii in range(N_TRACKS):
        for j in range(len(radar_y[ii])):
            radar_y[ii][j] -= y

        if ii == 1:
            start = track_2_start
        elif ii == 5:
            start = track_7_start
        else:
            start = 0

        for j in range(start, len(suitcase_speed[ii])):
            errs_lp_radar_speed_all.append(suitcase_speed[ii][j] - radar_speed[ii][j])

            # 0 -> 100 m
            if 0 <= radar_y[ii][j] < 50:
                errs_lp_radar_speed_incremental_meters[0].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 50 < radar_y[ii][j] <= 100:
                errs_lp_radar_speed_incremental_meters[1].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 100 < radar_y[ii][j] <= 150:
                errs_lp_radar_speed_incremental_meters[2].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 150 < radar_y[ii][j] <= 200:
                errs_lp_radar_speed_incremental_meters[3].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 200 < radar_y[ii][j] <= 300:
                errs_lp_radar_speed_incremental_meters[4].append(suitcase_speed[ii][j] - radar_speed[ii][j])

            # 0 -> 100 ft
            if 0 <= radar_y[ii][j] < 30.48:
                errs_lp_radar_speed_incremental_feet[0].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 30.48 < radar_y[ii][j] <= 60.96:
                errs_lp_radar_speed_incremental_feet[1].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 60.96 < radar_y[ii][j] <= 91.44:
                errs_lp_radar_speed_incremental_feet[2].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 91.44 < radar_y[ii][j] <= 121.92:
                errs_lp_radar_speed_incremental_feet[3].append(suitcase_speed[ii][j] - radar_speed[ii][j])
            elif 121.92 < radar_y[ii][j] <= 152.4:
                errs_lp_radar_speed_incremental_feet[4].append(suitcase_speed[ii][j] - radar_speed[ii][j])

        plt.scatter(range(len(suitcase_speed[ii][start:])), suitcase_speed[ii][start:], c='r', label='WAAS-GPS')
        plt.scatter(range(len(radar_speed[ii][start:])), radar_speed[ii][start:], c='b', label='radar')
        plt.xlabel(r'$\bigtriangleup$ t = 100 ms')
        plt.ylabel('meters/s')
        plt.ylim(ylims[ii][0], ylims[ii][1])
        plt.xlim(-20, 250)
        plt.legend(loc=4)
        plt.grid(True)
        plt.title('WAAS-GPS vs radar speed estimates\nRun %d' % (ii + 1))
        fig = plt.gcf()
        fig.set_size_inches(10, 6)
        fig.savefig('imgs/lp-vs-radar-speed-error-track-' + str(ii + 1) + '.png', dpi=100)
        plt.clf()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(errs_lp_radar_speed_all, bins=25)
    ax.set_xlabel('m/s')
    ax.set_title('Error between WAAS-GPS and radar speed estimates')
    fig.set_size_inches(8, 6)
    plt.grid(True)
    fig.savefig('imgs/lp-vs-radar-speed-error.png', dpi=100)

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between WAAS-GPS and radar speed estimates\n0 - 50 m", "50 - 100 m", "100 - 150 m",
              "150 - 200 m", "200 - 300 m"]
    for i in range(5):
        axarr[i].hist(errs_lp_radar_speed_incremental_meters[i], bins=15)
        axarr[i].set_title(titles[i])
        axarr[i].grid(True)
    axarr[-1].set_xlabel('m/s')
    fig.set_size_inches(8, 8)
    fig.savefig('imgs/lp-vs-radar-speed-incremental-meters.png', dpi=100)

    fig, axarr = plt.subplots(5, sharex=True)
    titles = ["Error between WAAS-GPS and radar speed estimates\n0 - 100 ft", "100 - 200 ft", "200 - 300 ft",
              "300 - 400 ft", "400 - 500 ft"]
    for i in range(5):
        axarr[i].hist(errs_lp_radar_speed_incremental_feet[i], bins=15)
        axarr[i].set_title(titles[i])
        axarr[i].grid(True)
    axarr[-1].set_xlabel('m/s')
    fig.set_size_inches(8, 8)
    fig.savefig('imgs/lp-vs-radar-speed-incremental-feet.png', dpi=100)