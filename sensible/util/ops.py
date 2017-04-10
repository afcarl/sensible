try:  # python 2.7
    import cPickle as pickle
except ImportError:  # python 3.5 or 3.6
    import pickle


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


def show(string, verbose):
    if verbose:
        print(string)
