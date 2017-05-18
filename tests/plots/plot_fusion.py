import matplotlib.pyplot as plt
import pandas as pd

if __name__ == '__main__':
    UTM = {'x': 365739.1602739443, 'y': 3277670.2727047433}

    df = pd.DataFrame.from_csv('../data/SW-42-SW-40/cleaned_trackLog_05-09-2017.csv')
    radar = df[df.TrackID == 4]
    radar_kf = radar[radar.Filtered == 1]

    dsrc = df[df.TrackID == 5]
    dsrc_fusion = dsrc[dsrc.Filtered == 2]
    dsrc_kf = dsrc[dsrc.Filtered == 1]

    fig = plt.figure(1)
    plt.plot(dsrc_kf['yPos'] - UTM['y'], c='b', label='WAAS-GPS')
    plt.plot(radar_kf['yPos'] - UTM['y'], c='r', label='Radar')
    plt.plot(dsrc_fusion['yPos'] - UTM['y'], c='k', label='Fused estimate')
    plt.annotate('Optimization begins', xy=(687, 3277838 - UTM['y']), xytext=(600, 3277900 - UTM['y']), arrowprops=dict(arrowstyle="->", connectionstyle="arc3"))

    plt.title('Covariance Intersection for range estimate between WAAS-GPS and radar')
    plt.ylabel('Range (meters)')
    plt.legend()
    plt.show()

    fig.set_size_inches(8, 8)
    fig.savefig('imgs/track-to-track-fusion.png', dpi=100)