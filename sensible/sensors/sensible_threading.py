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


class SocketThread(StoppableThread):
    """Used for receiving data measurements from a sensor."""

    def __init__(self, sensor, ip_address, port, msg_len, name):
        super(SocketThread, self).__init__(name)
        self._sensor = sensor
        self._ip_address = ip_address
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # open connection to incoming DSRC messages
        try:
            self._sock.bind((self._ip_address, self._port))
            self._sock.setblocking(0)
        except socket.error as e:
            print(e)

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

    def push(self, msg):
        """
        Push the msg through the processing pipeline.

        Needs to be defined by the subclass
        """
        self._sensor.push(msg)


class SerialThread(StoppableThread):

    def __init__(self, sensor, port, baud, name):
        super(SerialThread, self).__init__(name)
        self._ser = serial.Serial(port=port, baudrate=baud, timeout=0)
        self._sensor = sensor

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
        if len(data) < 64:
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
        incoming_data = []
        cars = []
        # Though at SMS we curently only see satusID of '06008', I though tto include others incase future radars start detecting differently.
        possible_satus_ids = ['050008', '058008', '060008', '068008']
        # Trigger positions
        # ALL measurements must be in meters.
        # ALL lane coordinates have to be with respect to the sensor, not the blue crossed origin.
        # Patrick: for a zone at SW 42nd SW 40th at -96 to -86 m in lane 1
        front_line_xs = [108.31]
        line_lengths = [10]
        # left with respect to the a drive driving in the lanes. SMS gives lane positions from the middle so the points have to be adjusted.
        left_line_ys = [5.3]
        line_width = 4.5   # 4.5 m
        trigger_offset = 0
        timeStampHold = ''
        timeStamp = ''
        car_width = 1.5
        status_id_type = ''

        cars_coming = False
        while not self.stopped():
            if cars_coming:
                if len(incoming_data) is 33:
                    if incoming_data[22] == status_id_type:
                        #print('timestamp Binary: ')
                        #print(incoming_data[0:11])
                        # should be 060008 then time stamp
                        for var in incoming_data[3:11]:
                            timeStampHold += var
                        BAD_TIME_STAMP = False
                        if timeStampHold == '':
                            BAD_TIME_STAMP = True
                        if not BAD_TIME_STAMP:
                            timeStampBin = bin(int((timeStampHold), 16))[2:]
                            if len(timeStampBin) < 64:
                                timeStampBin = SerialThread.addZeros(timeStampBin)
                            
                            #timeStamp = str(int(timeStampBin[0:8], 2)) + str(int(timeStampBin[8:16], 2)) + str(
                            #    int(timeStampBin[16:24], 2)) + str(int(timeStampBin[24:32], 2))
                            
                            timeStamp = int(timeStampBin[0:8], 2) << 0
                            timeStamp += int(timeStampBin[8:16], 2) << 8
                            timeStamp += int(timeStampBin[16:24], 2) << 16
                            timeStamp += int(timeStampBin[24:32], 2) << 24

                            timeStampHold = ''
                        binary_stuff = incoming_data[-8]
                        for var in incoming_data[-7:]:
                            binary_stuff += var
                        BAD_BINARY_STUFF = False
                        if binary_stuff == '':
                            BAD_BINARY_STUFF = True
                        if not BAD_TIME_STAMP and not BAD_BINARY_STUFF:
                            obtainedData = SerialThread.positionData(bin(int((binary_stuff), 16))[2:])
                            obtainedData['TimeStamp'] = str(timeStamp)
                            cars.append(obtainedData)
                            #ar_check
                            for box in range(len(front_line_xs)):
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
                        cars = []
                        cars_coming = False
            data = self._ser.read(1)
            incoming_data.append(binascii.hexlify(data).decode(encoding='UTF-8'))
            if len(incoming_data) > 3:
                last_three = (incoming_data[-3] + incoming_data[-2] + incoming_data[-1])
                if (last_three == possible_satus_ids[0] or (last_three == possible_satus_ids[1]) or (
                            last_three == possible_satus_ids[2]) or (last_three == possible_satus_ids[3])):
                    cars_coming = True
                    status_id_type = incoming_data[-3]
                    incoming_data = incoming_data[-3:]

    def push(self, msg):
        """
        Push the msg through the processing pipeline.

        Needs to be defined by the subclass
        """
        self._sensor.push(msg)
