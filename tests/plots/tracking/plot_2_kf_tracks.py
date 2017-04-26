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

    lane1_filtered_data = df.query('Filtered == 1 & TrackID == \'2E7C0E21\'')
    lane1_real_data = df.query('Filtered == 0 & TrackID == \'2E7C0E21\'')

    lane2_filtered_data = df.query('Filtered == 1 & TrackID == \'005F212C\'')
    lane2_real_data = df.query('Filtered == 0 & TrackID == \'005F212C\'')

    plt.figure(1)
    plt.subplot(141)
    plt.plot(lane1_filtered_data['xPos'], 'r')
    plt.plot(lane1_real_data['xPos'], 'b')
    plt.subplot(142)
    plt.plot(lane1_filtered_data['yPos'], 'r')
    plt.plot(lane1_real_data['yPos'], 'b')
    plt.subplot(143)
    plt.plot(lane1_filtered_data['xSpeed'], 'r')
    plt.plot(lane1_real_data['xSpeed'], 'b')
    plt.subplot(144)
    plt.plot(lane1_filtered_data['ySpeed'], 'r')
    plt.plot(lane1_real_data['ySpeed'], 'b')
    plt.title('Lane 1: Vehicle 2E7C0E21')
    plt.show()

    plt.figure(2)
    plt.subplot(141)
    plt.plot(lane2_filtered_data['xPos'], 'r')
    plt.plot(lane2_real_data['xPos'], 'b')
    plt.subplot(142)
    plt.plot(lane2_filtered_data['yPos'], 'r')
    plt.plot(lane2_real_data['yPos'], 'b')
    plt.subplot(143)
    plt.plot(lane2_filtered_data['xSpeed'], 'r')
    plt.plot(lane2_real_data['xSpeed'], 'b')
    plt.subplot(144)
    plt.plot(lane2_filtered_data['ySpeed'], 'r')
    plt.plot(lane2_real_data['ySpeed'], 'b')
    plt.title('Lane 2: Vehicle 005F212C')
    plt.show()


