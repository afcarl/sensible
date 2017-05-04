import argparse
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import pandas
import numpy as np


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Set run parameters.')

    parser.add_argument('--logfile', default='', help='Provide a .csv file containing tracks to plot')

    args = vars(parser.parse_args())

    df = pandas.read_csv(args['logfile'])
    df.drop(df[df.TrackState == 'ZOMBIE'].index, inplace=True)

    filtered_data = df.query('Filtered == 1 & TrackID == 3')
    real_data = df.query('Filtered == 0 & TrackID == 3')

    # for i in range(8):
    #track_i = filtered_data.loc[filtered_data['TrackID'] == i]
    #real_i = real_data.loc[real_data['TrackID'] == i]

    real_xPos = real_data['xPos'].as_matrix()
    filtered_xPos = filtered_data['xPos'].as_matrix()
    real_yPos = real_data['yPos'].as_matrix()
    filtered_yPos = filtered_data['yPos'].as_matrix()

    real_xSpeed = real_data['xSpeed'].as_matrix()
    filtered_xSpeed = filtered_data['xSpeed'].as_matrix()
    real_ySpeed = real_data['ySpeed'].as_matrix()
    filtered_ySpeed = filtered_data['ySpeed'].as_matrix()

    sum_sq_x = 0
    sum_sq_y = 0
    N_x = 0
    N_y = 0
    for i in range(len(real_xPos)):
        if not np.isnan(real_xPos[i]):
            sum_sq_x += abs(real_xPos[i] - filtered_xPos[i]) ** 2
            N_x += 1

    for i in range(len(real_yPos)):
        if not np.isnan(real_yPos[i]):
            sum_sq_y += abs(real_yPos[i] - filtered_yPos[i]) ** 2
            N_y += 1

    sum_sq_xSp = 0
    sum_sq_ySp = 0
    N_xSp = 0
    N_ySp = 0
    for i in range(len(real_xSpeed)):
        if not np.isnan(real_xSpeed[i]):
            sum_sq_xSp += abs(real_xSpeed[i] - filtered_xSpeed[i]) ** 2
            N_xSp += 1

    for i in range(len(real_ySpeed)):
        if not np.isnan(real_ySpeed[i]):
            sum_sq_ySp += abs(real_ySpeed[i] - filtered_ySpeed[i]) ** 2
            N_ySp += 1

    rms_x = np.sqrt(np.divide(sum_sq_x, N_x))
    rms_y = np.sqrt(np.divide(sum_sq_y, N_y))
    rms_xSp = np.sqrt(np.divide(sum_sq_xSp, N_xSp))
    rms_ySp = np.sqrt(np.divide(sum_sq_ySp, N_ySp))

    print("RMSE xPos: {}".format(rms_x))
    print("RMSE yPos: {}".format(rms_y))
    print("RMSE xSpeed: {}".format(rms_xSp))
    print("RMSE ySpeed: {}".format(rms_ySp))

    plt.figure(1)
    # plt.subplot(141)
    # plt.plot(filtered_data['xPos'], 'r')
    # plt.plot(real_data['xPos'], 'b')
    # plt.subplot(142)
    plt.plot(filtered_data['yPos'], 'r')
    plt.plot(real_data['yPos'], 'b')
    # plt.subplot(143)
    # plt.plot(filtered_data['xSpeed'], 'r')
    # plt.plot(real_data['xSpeed'], 'b')
    # plt.subplot(144)
    # plt.plot(filtered_data['ySpeed'], 'r')
    # plt.plot(real_data['ySpeed'], 'b')
    plt.show()



