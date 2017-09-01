try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle

import time
import os
from datetime import datetime

track_logger = None
system_logger = None


def verify(val, min_val, max_val):
    """If val < min or val > max, raise a ParseError

    :param val:
    :param min_val:
    :param max_val:
    :return:
    """
    if val < min_val or val > max_val:
        raise ValueError("Value {} out of min bound: {} "
                         "and max bound: {}".format(val, min_val, max_val))
    else:
        return val


def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val -= (1 << bits)  # compute negative value
    return val  # return positive value as is


def dump(content, filename):
    """
    pickle content to filename
    """
    try:
        with open(filename, 'wb') as outfile:
            pickle.dump(content, outfile)
            outfile.close()
    except IOError as e:
        print("Fail: error to open file: {}".format(filename))


def load_pkl(path):
    """
    Load pickled content from path
    :param path:
    :return:
    """
    with open(path, "rb") as f:
        obj = pickle.load(f)
    print("  [*] load {}\n".format(path))
    return obj


def merge_n_lists(big_list):
    """
    Merge a list of lists into a single list,
    interleaving the elements of each list in the final result.

    :param big_list:
    :return: a flattened list containing all elements of big_list interleaved evenly.
    """
    # no need to merge if there is only 1 list
    if type(big_list[0]) is not list:
        return big_list

    result = []
    lengths = []
    for m in big_list:
        lengths.append(len(m))
    while sum(lengths) > 0:
        for idx, m in enumerate(big_list):
            if lengths[idx] > 0:
                result.append(m[-lengths[idx]])
                lengths[idx] -= 1
    return result


def initialize_logs():
    global system_logger
    global track_logger

    if not os.path.isdir('logs'):
        os.mkdir('logs')

    if track_logger is None:
        # Track logger
        t = time.localtime()
        timestamp = time.strftime('%m-%d-%Y_%H%M', t)
        track_logger = open(os.path.join('logs', "trackLog_" + timestamp + ".csv"), 'wb')
        logger_title = b"TrackID,TrackState,Filtered,timestamp,xPos,xSpeed,yPos,ySpeed,Sensor,Served\n"
        track_logger.write(logger_title)
    if system_logger is None:
        # System logger
        t = time.localtime()
        timestamp = time.strftime('%m-%d-%Y_%H%M', t)
        system_logger = open(os.path.join('logs', "systemLog_" + timestamp + ".log"), 'wb')


def show(string, verbose):
    global system_logger
    if system_logger is None:
        print("  [!] Need to call ops.initialize_logs() first")
    else:
        ts = datetime.utcnow()
        ts = '[{}:{}:{}]'.format(ts.hour, ts.minute, (ts.second * 1000) + (ts.microsecond/1000))
        string = ts + string
        system_logger.write(string)
        if verbose:
            print(string)


def close_logs():
    global track_logger
    global system_logger
    if track_logger is not None:
        track_logger.close()
    if system_logger is not None:
        system_logger.close()


def replace_none(x, replace_with):
    if hasattr(x, 'len'):
        for i in range(len(x)):
            if x[i] is None:
                x[i] = replace_with
    else:
        if x is None:
            return replace_with
    return x

