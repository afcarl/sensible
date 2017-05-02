from __future__ import absolute_import
import threading
import socket
import serial
import binascii


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, name):
        super(StoppableThread, self).__init__(name=name)
        self._stopper = threading.Event()

    def stop(self):
        """Stop the DSRC thread."""
        self.stop_thread()
        self.join()

    def stop_thread(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.is_set()


class SensorThread(StoppableThread):
    """Used for receiving data measurements from a sensor."""

    def __init__(self, ip_address, port, msg_len, name):
        super(SensorThread, self).__init__(name)
        self._ip_address = ip_address
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._msg_len = msg_len

    def run(self):
        """Main method for Stoppable thread"""
        while not self.stopped():
            try:
                msg, address = self._sock.recvfrom(self._msg_len)
            except socket.error as err:
                continue

            try:
                self.push(msg)
            except Exception as e:
                continue

        self._sock.close()

    def connect(self):
        # open connection to incoming DSRC messages
        try:
            self._sock.bind((self._ip_address, self._port))
            self._sock.setblocking(0)
        except socket.error as e:
            print(e)

    def push(self, msg):
        """
        Push the msg through the processing pipeline.

        Needs to be defined by the subclass
        """
        raise NotImplementedError

    @staticmethod
    def topic():
        """All sensors make accessible the topic of the message they are publishing."""
        raise NotImplementedError

    @staticmethod
    def get_filter(dt):
        """
        Returns an instance of an object
        that configures a KalmanFilter for this specific Sensor
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def bsm(track_id, track):
        """Return a string containing the relevant information to generate a BSM.

        Should contain the following CSVs:
        1. ID
        2. H
        3. M
        4. S
        5. xPos (UTM easting)
        6. yPos (UTM northing)
        7. speed
        8. lane
        9. vehicle length
        10. max accel
        11. max decel
        12. served
        """
        raise NotImplementedError

    @staticmethod
    def get_default_vehicle_type(**kwargs):
        """
        Return the default vehicle type given the arguments.
        :return:
        """
        raise NotImplementedError


class SerialThread(StoppableThread):

    def __init__(self, port, baud, name):
        super(SerialThread, self).__init__(name)
        self.ser = serial.Serial(port=port, baudrate=baud, timeout=0)

    @staticmethod
    def addZeros(data):
        subStr = ''
        newStr = ''
        for i in range(0, (64 - len(data))):
            subStr += '0'
        newStr += subStr
        newStr += data
        return newStr

    @staticmethod
    def positionData(data):
        if (len(data) < 64):
            # subStr = ''
            # newStr = ''
            # for i in range(0,(64-len(data))):
            # subStr += '0'
            # newStr += subStr
            # newStr += data
            data = SerialThread.addZeros(data)
        # objNum is general the car closest to the sensor
        # objNum = num
        # objID should stay with the object from when it is recognized until it has left the view of the radar. Almost always works.
        objID = int(data[:6], 2)
        objLength = (int(data[6:14], 2) * 0.2)
        yposvel = ((int(data[14:25], 2) - 1024) * 0.1)
        xposvel = ((int(data[25:36], 2) - 1024) * 0.1)
        ypos = ((int(data[36:50], 2) - 8192) * 0.064)
        xpos = ((int(data[50:64], 2) - 8192) * 0.064)

        InterprettedArray = {'objMessage': 'Track', 'objID': objID, 'objLength': objLength, 'yVel': yposvel,
                             'xVel': xposvel, 'yPos': ypos, 'xPos': xpos, 'TimeStamp': '', 'objZone': -1}
        return InterprettedArray

    def run(self):
        """Main method for Stoppable thread"""
        while not self.stopped():
            incoming_data = []
            cars = []
            # Though at SMS we curently only see satusID of '06008', I though tto include others incase future radars start detecting differently.
            possible_satus_ids = ['050008', '058008', '060008', '068008']
            # Trigger positions
            # ALL measurements must be in meters.
            # ALL lane coordinates have to be with respect to the sensor, not the blue crossed origin.
            front_line_xs = [28.07, 27.78, 27.37, 27.33, 73.51, 73.1, 73.06, 119.24, 118.83, 118.79]
            line_lengths = [14.02, 14.33, 14.63, 14.63, 14.63, 14.33, 14.33, 13.72, 13.72, 13.72]
            # left with respect to the a drive driving in the lanes. SMS gives lane positions from the middle so the points have to be adjusted.
            left_line_ys = [-5.585, -2.136, 1.274, 4.734, -2.136, 1.274, 4.734, -2.136, 1.274, 4.734]
            line_width = 3.35
            trigger_offset = .75
            timeStampHold = ''
            timeStamp = ''
            car_width = 1.5
            status_id_type = ''
            stay = True
            cars_coming = False
            while stay:
                if cars_coming:
                    if len(incoming_data) is 33:
                        if incoming_data[22] == status_id_type:
                            for var in incoming_data[3:11]:
                                timeStampHold += var
                            timeStampBin = bin(int((timeStampHold), 16))[2:]
                            timeStampBinZeros = SerialThread.addZeros(timeStampBin)
                            timeStamp = str(int(timeStampBinZeros[0:8], 2)) + str(
                                int(timeStampBinZeros[8:16], 2)) + str(
                                int(timeStampBinZeros[16:24], 2)) + str(int(timeStampBinZeros[24:32], 2))
                            # print('TIME: ')
                            # print(timeStamp)
                            binary_stuff = incoming_data[-8]
                            for var in incoming_data[-7:]:
                                binary_stuff += var
                            obtainedData = SerialThread.positionData(bin(int((binary_stuff), 16))[2:])
                            obtainedData['TimeStamp'] = timeStamp
                            cars.append(obtainedData)
                            # car_check
                            for box in range(0, 10):
                                if (((front_line_xs[box] + line_lengths[box]) >= float(obtainedData['xPos']) >=
                                         front_line_xs[
                                             box] or (front_line_xs[box] + line_lengths[box]) >= (
                                            float(obtainedData['xPos']) + float(obtainedData['objLength'])) >=
                                    front_line_xs[
                                        box] or (
                                            front_line_xs[box] + line_lengths[box]) <= (
                                            float(obtainedData['xPos']) + float(obtainedData['objLength'])) and float(
                                    obtainedData['xPos']) <= front_line_xs[box]) and (
                                                        (left_line_ys[box] + line_width - trigger_offset) >= float(
                                                        obtainedData['yPos']) - (car_width / 2) >= (
                                                            left_line_ys[box] + trigger_offset) or (
                                                            left_line_ys[box] + line_width - trigger_offset) >= (
                                                        float(obtainedData['yPos']) + (car_width / 2)) >= (
                                                        left_line_ys[box] + trigger_offset) or (
                                                        left_line_ys[box] + line_width - trigger_offset) <= (
                                                    float(obtainedData['yPos']) + (car_width / 2)) and (
                                                    float(obtainedData['yPos']) - (car_width / 2)) <= (
                                                    left_line_ys[box] + trigger_offset))):
                                    tracked_car = dict(obtainedData)
                                    tracked_car['objMessage'] = 'Trigger'
                                    tracked_car['objZone'] = box
                                    cars.append(tracked_car)

                            incoming_data = incoming_data[:-11]
                        else:
                            incoming_data = []
                            try:
                                self.push(cars)
                            except ValueError as e:
                                continue
                            cars_coming = False
                data = self.ser.read(1)
                incoming_data.append(binascii.hexlify(data).decode(encoding='UTF-8'))
                if len(incoming_data) > 3:
                    last_three = (
                    incoming_data[len(incoming_data) - 3] + incoming_data[len(incoming_data) - 2] + incoming_data[
                        len(incoming_data) - 1])
                    if (last_three == possible_satus_ids[0] or (last_three == possible_satus_ids[1]) or (
                                last_three == possible_satus_ids[2]) or (last_three == possible_satus_ids[3])):
                        cars_coming = True
                        status_id_type = incoming_data[len(incoming_data) - 3]
                        incoming_data = incoming_data[-3:]

    def push(self, msg):
        """
        Push the msg through the processing pipeline.

        Needs to be defined by the subclass
        """
        raise NotImplementedError

    @staticmethod
    def topic():
        """All sensors make accessible the topic of the message they are publishing."""
        raise NotImplementedError

    @staticmethod
    def get_filter(dt):
        """
        Returns an instance of an object
        that configures a KalmanFilter for this specific Sensor
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def bsm(track_id, track):
        """Return a string containing the relevant information to generate a BSM.

        Should contain the following CSVs:
        1. ID
        2. H
        3. M
        4. S
        5. xPos (UTM easting)
        6. yPos (UTM northing)
        7. speed
        8. lane
        9. vehicle length
        10. max accel
        11. max decel
        12. served
        """
        raise NotImplementedError

    @staticmethod
    def get_default_vehicle_type(**kwargs):
        """
        Return the default vehicle type given the arguments.
        :return:
        """
        raise NotImplementedError