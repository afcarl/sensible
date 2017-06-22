# This script accepts an ip address and port number to forward the radar data to
import socket
import argparse 
import cPickle as pickle
import serial


def addZeros(data):
    subStr = ''
    newStr = ''
    for i in range(0, (64 - len(data))):
        subStr += '0'
    newStr += subStr
    newStr += data
    return newStr

def positionData(data):
    if len(data) < 64:
        # subStr = ''
        # newStr = ''
        # for i in range(0,(64-len(data))):
        # subStr += '0'
        # newStr += subStr
        # newStr += data
        data = addZeros(data)
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

def run(ip_address, port, sock, ser):
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
    while True:
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
                            timeStampBin = addZeros(timeStampBin)
                        
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
                        obtainedData = positionData(bin(int((binary_stuff), 16))[2:])
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
                        sock.sendto(pickle.dumps(cars), (ip_address, port))
                    except ValueError as e:
                        continue
                    cars = []
                    cars_coming = False
        data = ser.read(1)
        incoming_data.append(binascii.hexlify(data).decode(encoding='UTF-8'))
        if len(incoming_data) > 3:
            last_three = (incoming_data[-3] + incoming_data[-2] + incoming_data[-1])
            if (last_three == possible_satus_ids[0] or (last_three == possible_satus_ids[1]) or (
                        last_three == possible_satus_ids[2]) or (last_three == possible_satus_ids[3])):
                cars_coming = True
                status_id_type = incoming_data[-3]
                incoming_data = incoming_data[-3:]

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--ip', default='', help='')
	parser.add_argument('--port', type=int, default=4200)
	parser.add_argument('--serial-port', default='/dev/ttyUSB0')
	parser.add_argument('--baud-rate', type=int, default=115200)

	args = vars(parser.parse_args())

	# establish socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setblocking(0)

	try:
		# establish serial connection
		ser = serial.Serial(port=args['serial_port'], baudrate=args['baud_rate'], timeout=0)
	except:
		print('Unable to connect serial port!')
		exit(1)

	run(args['ip'], args['port'], sock, ser)