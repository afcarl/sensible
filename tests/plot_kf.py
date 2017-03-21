import argparse
import matplotlib
matplotlib.use('Qt4Agg')

import matplotlib.pyplot as plt
import pandas


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set run parameters.')

    parser.add_argument('--logfile', default='', help='Provide a .csv file containing tracks to plot')

    args = vars(parser.parse_args())

    df = pandas.read_csv(args['logfile'])

    filtered_data = df.loc[df['Filtered'] == 1]
    real_data = df.loc[df['Filtered'] == 0]

    plt.figure(1)
    plt.subplot(141)
    plt.plot(filtered_data['xPos'], 'r')
    plt.plot(real_data['xPos'], 'b')
    plt.subplot(142)
    plt.plot(filtered_data['yPos'], 'r')
    plt.plot(real_data['yPos'], 'b')
    plt.subplot(143)
    plt.plot(filtered_data['xSpeed'], 'r')
    plt.plot(real_data['xSpeed'], 'b')
    plt.subplot(144)
    plt.plot(filtered_data['ySpeed'], 'r')
    plt.plot(real_data['ySpeed'], 'b')
    plt.show()



