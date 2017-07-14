from __future__ import absolute_import

import argparse
import sensible.util.ops as ops
import xml.etree.cElementTree as ElementTree
import socket
from datetime import datetime
import time


def parse(msg):
    """Convert msg data from hex to decimal and filter msgs.

    Messages with the Served field set to 1 or that are unreadable
    will be dropped. We assume the messages are arriving in proper XML
    format.

    :param msg:
    :return: parsed_msg
    """
    msg = msg.split("\n", 1)
    timestamp = msg[0]
    msg = msg[1]

    try:
        root = ElementTree.fromstring(msg)
    except ElementTree.ParseError:
        raise Exception("Unable to parse msg")

    blob1 = root.find('blob1')
    data = ''.join(blob1.text.split())

    # convert hex values to decimal
    msg_count = int(data[0:2], 16)
    veh_id = int(data[2:10], 16)
    h = ops.verify(int(data[10:12], 16), 0, 23)
    m = ops.verify(int(data[12:14], 16), 0, 59)
    s = ops.verify(int(data[14:18], 16), 0, 60000)  # ms
    lat = ops.verify(ops.twos_comp(int(data[18:26], 16), 32), -900000000, 900000000) * 1e-7
    lon = ops.verify(ops.twos_comp(int(data[26:34], 16), 32), -1799999999, 1800000000) * 1e-7
    heading = ops.verify(int(data[34:38], 16), 0, 28799) * 0.0125
    rms_lat = int(data[38:42], 16) * 0.01
    rms_lon = int(data[42:46], 16) * 0.01
    speed = ops.verify(int(data[46:50], 16), 0, 8190) * 0.02  # m/s
    lane = int(data[50:52], 16)
    veh_len = ops.verify(int(data[52:56], 16), 0, 16383) * 0.01  # m
    max_accel = ops.verify(int(data[56:60], 16), 0, 2000) * 0.01  # m/s^2
    max_decel = ops.verify(int(data[60:64], 16), 0, 2000) * -0.01  # m/s^2
    served = int(data[64:66], 16)

    return {
        'msg_count': msg_count,
        'id': veh_id,
        'h': h,
        'm': m,
        's': s,
        'lat': lat,
        'lon': lon,
        'heading': heading,
        'rms_lat': rms_lat,
        'rms_lon': rms_lon,
        'speed': speed,
        'lane': lane,
        'veh_len': veh_len,
        'max_accel': max_accel,
        'max_decel': max_decel,
        'served': served
    }, timestamp


if __name__ == '__main__':
    MSG_LEN = 277
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default='', help='[DEBUG] Provide a valid path to a DSRC log file')
    parser.add_argument('--ip', default='169.254.117.14', help='Radio IP')
    parser.add_argument('--p', default=4200, help='Radio port')
    parser.add_argument('--run-for', default=10, help='Num seconds to run app for')

    args = vars(parser.parse_args())

    if args['file'] != '':
        count = 0.
        avg_time_diff = 0.

        with open(args['file'], 'rb') as f:
            msgs = f.read().split('<START>')

            for msg in msgs:
                if msg == '\t' or msg == '':
                    continue
                try:
                    msg, radio_ts = parse(msg)
                except Exception as e:
                    continue
                dt = datetime.utcnow()
                hour = '{:02}'.format(dt.hour)
                minute = '{:02}'.format(dt.minute)
                ms = '{:04}'.format(int(dt.second * 1000 + round(dt.microsecond / 1000)))
                print(
                'Suitcase time: {}, GPS time: {}:{}:{}, Server time: {}:{}:{}'.format(radio_ts, msg['h'], msg['m'], msg['s'], hour, minute, ms))
                GPS_server_time_diff_seconds = ((dt.hour * 3600.) + (dt.minute * 60) + int(
                    dt.second * 1000 + round(dt.microsecond / 1000)) / 1000.) - (
                                    (msg['h'] * 3600) + (msg['m'] * 60) + msg['s'] / 1000.)

                struct_time = time.strptime(radio_ts, '%Y:%m:%d %H:%M:%S:%f')
                Radio_GPS_time_diff_seconds = ((struct_time[3] * 3600.) + (struct_time[4] * 60) + struct_time[5]) - \
                                              ((msg['h'] * 3600) + (msg['m'] * 60) + msg['s'] / 1000.)

                count += 1
                avg_time_diff += ((Radio_GPS_time_diff_seconds + GPS_server_time_diff_seconds) / count)

                print('Suitcase -> GPS time diff: {}, GPS -> Server time diff: {}, avg time diff: {}'.format(
                    Radio_GPS_time_diff_seconds, GPS_server_time_diff_seconds, avg_time_diff))
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((args['ip'], int(args['p'])))
        sock.setblocking(0)
        start = time.time()
        avg_time_diff = 0.
        count = 0.
        while time.time() - start < float(args['run_for']):
            try:
                data, address = sock.recvfrom(MSG_LEN)
                try:
                    msg, radio_ts = parse(data)
                except Exception as ex:
                    continue
                dt = datetime.utcnow()
                hour = '{:02}'.format(dt.hour)
                minute = '{:02}'.format(dt.minute)
                ms_ = int(dt.second * 1000 + round(dt.microsecond / 1000))
                ms = '{:04}'.format(ms_)

                print(
                    'Suitcase time: {}, GPS time: {}:{}:{}, Server time: {}:{}:{}'.format(radio_ts, msg['h'], msg['m'],
                                                                                          msg['s'], hour, minute, ms))
                GPS_server_time_diff_seconds = ((dt.hour * 3600.) + (dt.minute * 60) + int(
                    dt.second * 1000 + round(dt.microsecond / 1000)) / 1000.) - (
                                                   (msg['h'] * 3600) + (msg['m'] * 60) + msg['s'] / 1000.)

                struct_time = time.strptime(radio_ts, '%Y:%m:%d %H:%M:%S:%f')
                Radio_GPS_time_diff_seconds = ((struct_time[3] * 3600.) + (struct_time[4] * 60) + struct_time[5]) - \
                                              ((msg['h'] * 3600) + (msg['m'] * 60) + msg['s'] / 1000.)

                count += 1
                avg_time_diff += ((Radio_GPS_time_diff_seconds + GPS_server_time_diff_seconds) / count)

                print('Suitcase -> GPS time diff: {}, GPS -> Server time diff: {}, avg time diff: {}'.format(
                    Radio_GPS_time_diff_seconds, GPS_server_time_diff_seconds, avg_time_diff))

            except socket.error:
                continue

        sock.close()
