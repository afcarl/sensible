def unavailable():
    return "UNAVAILABLE"


class TimeStamp:

    def __init__(self, h, m, s):
        self.h = h
        self.m = m
        self.s = s

    def to_string(self):
        return "{}:{}:{}".format(self.h, self.m, int(float(self.s)))

    def to_fname_string(self):
        return "{}-{}-{}".format(self.h, self.m, int(float(self.s)))

