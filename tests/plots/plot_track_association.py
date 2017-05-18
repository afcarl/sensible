import matplotlib.pyplot as plt
import gaussPlot2d
import numpy as np

"""
3,CONFIRMED,1,18:4:20224,3277746.80981,-12.348043338,Radar
3,CONFIRMED,0,18:4:20224,3277747.4567,-12.2,Radar
4,CONFIRMED,1,18:4:20329,3277930.04858,-10.4955549268,Radar
4,CONFIRMED,0,18:4:20329,3277928.8967,-10.6,Radar
5,CONFIRMED,2,18:4:19800,365739.181451,0.0684872170914,3277930.04858,-10.4955549268,DSRC
5,CONFIRMED,1,18:4:19800,365739.181451,0.0684872170914,3277935.01596,-10.227966282,DSRC
5,CONFIRMED,0,18:4:19800,365739.180885,0.0426949945601,3277936.6296,-10.2999115111,DSRC
6,CONFIRMED,1,18:4:20224,3277816.69992,-5.17321327795,Radar
6,CONFIRMED,0,18:4:20224,3277816.0647,-5.2,Radar
"""

"""
23,CONFIRMED,1,18:16:50400,365738.741519,0.108432312095,3277958.95155,-12.7852808187,DSRC
23,CONFIRMED,0,18:16:50400,365738.741023,0.0701400715612,3277958.94582,-12.8598087222,DSRC
24,CONFIRMED,1,18:16:50700,3277951.24602,-12.9089678239,Radar
24,CONFIRMED,0,18:16:50700,3277952.8967,-12.9,Radar
"""

if __name__ == '__main__':
    z = 3.49
    UTM = {'x': 365739.1602739443, 'y': 3277670.2727047433}

    mu1 = np.array([[3277935.01596 - UTM['y']], [-10.227966282]])
    sigma1 = np.array([[(6.02 / z) ** 2, 0], [0, (1 / z) ** 2]])

    mu2 = np.array([[3277930.04858 - UTM['y']], [-10.4955549268]])
    sigma2 = np.array([[(5 / z) ** 2, 0], [0, (0.5 / z) ** 2]])

    mu3 = np.array([[3277958.95155 - UTM['y']], [-12.7852808187]])
    sigma3 = np.array([[(6.02 / z) ** 2, 0], [0, (1 / z) ** 2]])

    mu4 = np.array([[3277951.24602 - UTM['y']], [-12.9089678239]])
    sigma4 = np.array([[(5 / z) ** 2, 0], [0, (0.5 / z) ** 2]])

    fig = plt.figure(1)

    gaussPlot2d.gauss_plot_2d(mu1, sigma1, chi_square=9.488, label='WAAS-GPS', color='b', annotation='18:4:19800')
    gaussPlot2d.gauss_plot_2d(mu2, sigma2, chi_square=9.488, label='Radar', color='y', annotation='18:4:20329')

    plt.title("WAAS-GPS to Radar TTTA")
    plt.xlabel("Range (meters)")
    plt.ylabel("Speed (meters/sec)")
    plt.legend()

    fig.set_size_inches(8, 8)
    fig.savefig('imgs/ttta.png', dpi=100)
    plt.close()

