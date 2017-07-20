import pandas as pd
import os
import numpy as np
import cPickle as pickle
import ops 

DROPBOX_DIR="C:\Users\Patrick\\"
#GPS_DIR=os.path.join(DROPBOX_DIR, "Dropbox (UFL)", "Data", "SW-42nd-SW-40-Radar-Installation", "Vehicle GPS", "Gainesville Intersection GPS")
GPS_DIR=os.path.join(DROPBOX_DIR, "Dropbox (UFL)", "Data", "SW-16-SW-13")
GPS_FILES=["CDGPSrun1"]
#GPS_FILES=["Test1", "Test2", "Test3", "Test4", "Test5", "Test6", "Test7"]
#GPS_FILES=["Test1"]
#DEST_DIR="C:\Users\Patrick\Github\FDOT-Intersection-Controller\cfg\SW-42nd-SW-40th\GPS"
DEST_DIR=os.path.join(DROPBOX_DIR, "Dropbox (UFL)", "Data", "SW-16-SW-13", "Cleaned DSRC")
#DEST_DIR=os.path.join(DROPBOX_DIR, "Dropbox (UFL)", "Data", "SW-42nd-SW-40-Radar-Installation", "Cleaned DSRC")

"""
GPS_TS = [('1900-01-01 18:50:38.8', '1900-01-01 18:51:00.4'),
          ('1900-01-01 18:44:44.0', '1900-01-01 18:45:05.4'),
          ('1900-01-01 18:42:14.4', '1900-01-01 18:42:20.4'),
          ('1900-01-01 18:47:18.2', '1900-01-01 18:47:28.2')]
"""
GPS_TS = [("1900-01-01 18:25:10.0", "1900-01-01 18:25:32.0"),
          ("1900-01-01 18:28:11.0", "1900-01-01 18:28:34.8"),
          ("1900-01-01 18:32:05.0", "1900-01-01 18:32:26.8"),
          ("1900-01-01 18:36:05.2", "1900-01-01 18:36:28.2"),
          ("1900-01-01 18:39:40.8", "1900-01-01 18:39:55.0"),
          ("1900-01-01 18:42:35.5", "1900-01-01 18:42:53.2")]


def interpolate(r_df, r_idx, values):
    rs = pd.DataFrame(index=r_idx)
    idx_after = np.searchsorted(r_df.index.values, rs.index.values)

    for v in values:
        rs['after'] = r_df.loc[r_df.index[idx_after], v].values
        rs['before'] = r_df.loc[r_df.index[idx_after - 1], v].values
        rs['after_time'] = r_df.index[idx_after]
        rs['before_time'] = r_df.index[idx_after - 1]

        # calculate new weighted value
        rs['span'] = (rs['after_time'] - rs['before_time'])
        rs['after_weight'] = (rs['after_time'] - rs.index) / rs['span']
        # I got errors here unless I turn the index to a series
        rs['before_weight'] = (pd.Series(data=rs.index, index=rs.index) - rs['before_time']) / rs['span']

        rs[v] = rs.eval('before * before_weight + after * after_weight')
    return rs

if __name__ == '__main__':

    # gps = pd.DataFrame.from_csv(os.path.join(GPS_DIR, GPS_FILES[3] + '.csv'), index_col=None)
    # x, y = gps['nfmlat'], gps['nfmlon']
    # for i in range(len(x)):
    #     print str(x[i]) + ',' + str(y[i])

    for ii, gps_file in enumerate(GPS_FILES):

        gps = pd.DataFrame.from_csv(os.path.join(GPS_DIR, gps_file + '.csv'), index_col=None)

        gps_utctime_vals = gps['utctime'].values.astype(np.float64)
        start = gps_utctime_vals[0]
        current = start
        t = 0.0
        t_delta = 0.1
        for i in range(len(gps_utctime_vals)):
            if gps_utctime_vals[i] != current:
                t = 0.0
                current = gps_utctime_vals[i]
            gps_utctime_vals[i] += t
            t += t_delta

        gps['utctime'] = pd.DataFrame(gps_utctime_vals)
        # parse the datetime
        gps['utctime'] = pd.to_datetime(gps['utctime'], format="%H%M%S.%f")
        # extend gps time by adding time increments of 50 ms
        #gps = gps.set_index('utctime')
        #idx_g = pd.date_range(start=GPS_TS[ii][0], end=GPS_TS[ii][1], freq='50ms')

        #interp_gps = interpolate(gps, idx_g, ['nlat', 'nlon'])

        #out = pd.concat([interp_gps['nlat'], interp_gps['nlon']], axis=1)
        #out.columns = ['Latitude', 'Longitude']
        out = pd.concat([gps['utctime'], gps['nfmspeed'], gps['nfmlat'], gps['nfmlon'], gps['nfmyaw']], axis=1)
        out.columns = ['utctime', 'speed', 'latitude', 'longitude', 'heading']
        #out.to_csv(os.path.join(DEST_DIR, gps_file + '.csv'), index=False)
        ops.dump(out, os.path.join(DEST_DIR, gps_file + '.pkl'))
