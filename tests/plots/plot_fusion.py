import matplotlib.pyplot as plt
import pandas as pd

if __name__ == '__main__':
    df = pd.DataFrame.from_csv('../data/SW-42-SW-40/cleaned_trackLog_05-09-2017.csv')
    radar = df[df.TrackID == 4]
    radar_kf = radar[radar.Filtered == 1]

    dsrc = df[df.TrackID == 5]
    dsrc_fusion = dsrc[dsrc.Filtered == 2]
    dsrc_kf = dsrc[dsrc.Filtered == 1]

    plt.figure(1)
    plt.plot(dsrc_kf['yPos'], c='b', label='DSRC')
    plt.plot(radar_kf['yPos'], c='r', label='Radar')
    plt.plot(dsrc_fusion['yPos'], c='k', label='Fused estimate')
    plt.annotate('Optimization begins', xy=(687, 3277838), xytext=(600, 3277900), arrowprops=dict(arrowstyle="->", connectionstyle="arc3"))

    plt.title('Track-to-track fusion for DSRC and radar')
    plt.xlabel('message index')
    plt.ylabel('Range (meters)')
    plt.legend()

    plt.show()