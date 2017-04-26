import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import sensible.util.ops as ops

N_TRACKS = 6

if __name__ == '__main__':
    radar_y = ops.load_pkl('radar_y.pkl')
    gps_y = ops.load_pkl('gps_y.pkl')
    suitcase_y = ops.load_pkl('suitcase_gps_y.pkl')

    radar_x = ops.load_pkl('radar_x.pkl')
    gps_x = ops.load_pkl('gps_x.pkl')
    suitcase_x = ops.load_pkl('suitcase_gps_x.pkl')

    radar_speed = ops.load_pkl('radar_speed.pkl')
    suitcase_speed = ops.load_pkl('suitcase_speed.pkl')
    suitcase_heading = ops.load_pkl('suitcase_heading.pkl')

    errs_y = []
    errs_x = []
    errs_hp_radar_range_all = []
    errs_lp_radar_range_all = []
    errs_lp_radar_speed_all = []

    track_2_start = 27
    track_7_start = 10
    for ii in range(N_TRACKS):
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
            idx_y += 1

        idx_x = 0
        # Suitcase vs HP GPS easting error
        for x1, x2 in zip(suitcase_x[ii], gps_x[ii]):
            if idx_x < start:
                idx_x += 1
                continue
            errs_x.append(x2 - x1)
            idx_x += 1

        # compare range of HP GPS and radar for all tracks
        for y1, y2 in zip(gps_y[ii], radar_y[ii]):
            errs_hp_radar_range_all.append(y1 - y2)

        idx = 0
        for y1, y2 in zip(suitcase_y[ii], radar_y[ii]):
            if idx < start:
                idx += 1
                continue
            errs_lp_radar_range_all.append(y1 - y2)
            idx += 1

        for j in range(start, len(suitcase_speed[ii])):
            errs_lp_radar_speed_all.append(-suitcase_speed[ii][j] - radar_speed[ii][j])

        plt.scatter(range(len(suitcase_speed[ii][start:])), suitcase_speed[ii][start:], c='r', label='suitcase')
        plt.scatter(range(len(radar_speed[ii][start:])), radar_speed[ii][start:], c='b', label='radar')
        plt.show()

        # fig, axarr = plt.subplots(2, sharex=False)
        # axarr[0].hist(errs_y, bins=15)
        # axarr[0].set_title('High-precision vs Low-precision GPS relative error in UTM northing')
        # axarr[1].hist(errs_x, bins=15)
        # axarr[1].set_title('High-precision vs Low-precision GPS relative error in UTM easting')

        # plt.show()

        # plt.hist(errs_hp_radar_range_all, bins=25)
        # plt.show()

        # plt.hist(errs_lp_radar_range_all, bins=25)
        # plt.show()
        # plt.hist(errs_lp_radar_speed_all, bins=20)
        # plt.show()