import serial
import binascii
import csv

ser = serial.Serial(port='COM13',baudrate=115200)
ser.timeout = 2

def write_csv(data):
    with open('cabinetTest_5_1_trigger_test.csv','w+') as csvfile:
        fieldnames = ['objMessage','objID','objLength','yVel','xVel','yPos','xPos','TimeStamp','objZone']
        writing = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writing.writeheader()
        for val in data:
            writing.writerow(val)

def positionData(data):

    if( len(data) < 64 ):
        subStr = ''
        newStr = ''
        for i in range(0,(64-len(data))):
            subStr += '0'
        newStr += subStr
        newStr += data
        data = newStr
    #objNum is general the car closest to the sensor
    #objNum = num
    #objID should stay with the object from when it is recognized until it has left the view of the radar. Almost always works.
    objID = int(data[:6], 2)
    objLength = (int(data[6:14], 2)* 0.2)
    yposvel = ((int(data[14:25], 2) - 1024) * 0.1)
    xposvel = ((int(data[25:36], 2) - 1024) * 0.1)
    ypos = ((int(data[36:50], 2) - 8192) * 0.064)
    xpos = ((int(data[50:64], 2) - 8192) * 0.064)

    InterprettedArray = {'objMessage':'Track','objID':objID,'objLength':objLength,'yVel':yposvel,'xVel':xposvel,'yPos':ypos,'xPos':xpos,'TimeStamp':'','objZone':-1}
    return InterprettedArray

#below I am finding the on coming cars by looking for the status id that would signify the list of cars is on its way(these are in possible_status ID)
#I found the status ids in the documentation from SMS
#I collect the data through pyserial .read() function and take the data from that return(example feedback: b'06')
# I then interpret the car data by splitting up the data into bits according to how the documentation says the should be split
#when the car is finished being read, I cut it off the array and wait until the next car is finished being loaded in(This is known from the length of the array)
#Finally, at the moment I print to CSV to make sure the data is correrct
if ser.is_open:
    incoming_data = []
    cars = []
    #Though at SMS we curently only see satusID of '06008', I though tto include others incase future radars start detecting differently. 
    possible_satus_ids = ['050008','058008','060008','068008']
    #Trigger positions
    #ALL measurements must be in meters.
    #ALL lane coordinates have to be with respect to the sensor, not the blue crossed origin.
    front_line_xs = [28.07,27.78,27.37,27.33,73.51,73.1,73.06,119.24,118.83,118.79]
    line_lengths = [14.02,14.33,14.63,14.63,14.63,14.33,14.33,13.72,13.72,13.72]
    #left with respect to the a drive driving in the lanes. SMS gives lane positions from the middle so the points have to be adjusted.
    left_line_ys = [-5.585,-2.136,1.274,4.734,-2.136,1.274,4.734,-2.136,1.274,4.734]
    line_width = 3.35
    trigger_offset = .75
    timeStampHold = ''
    timeStamp = ''
    car_width = 1.5
    status_id_type = ''
    stay= True
    cars_coming = False
    while stay:
        if cars_coming:
            if len(incoming_data) is 33:
                if incoming_data[22] == status_id_type:
                    print('timestamp Binary: ')
                    print(incoming_data[0:11])
                    #should be 060008 then time stamp
                    for var in incoming_data[3:11]:
                        timeStampHold+=var
                    timeStampBin = bin(int((timeStampHold), 16))[2:]
                    timeStampHold = ''
                    if (len(timeStampBin) < 64):
                        subStr = ''
                        newStr = ''
                        for i in range(0, (64 - len(data))):
                            subStr += '0'
                        newStr += subStr
                        newStr += timeStampBin
                        timeStampBinZeros = newStr
                    timeStamp = str(int(timeStampBinZeros[0:8],2))+str(int(timeStampBinZeros[8:16],2))+str(int(timeStampBinZeros[16:24],2))+str(int(timeStampBinZeros[24:32],2))
                    print('TIME: ')
                    print(timeStamp)
                    binary_stuff = incoming_data[-8]
                    for var in incoming_data[-7:]:
                        binary_stuff += var
                    obtainedData = positionData(bin(int((binary_stuff), 16))[2:])
                    obtainedData['TimeStamp'] = timeStamp
                    cars.append(obtainedData)
                    #car_check
                    for box in range(0,10):
                        if(((front_line_xs[box]+line_lengths[box]) >= float(obtainedData['xPos']) >= front_line_xs[box] or (front_line_xs[box]+line_lengths[box]) >= (float(obtainedData['xPos'])+float(obtainedData['objLength'])) >= front_line_xs[box] or (front_line_xs[box]+line_lengths[box]) <= (float(obtainedData['xPos'])+float(obtainedData['objLength'])) and float(obtainedData['xPos']) <= front_line_xs[box]) and ( (left_line_ys[box]+line_width-trigger_offset) >= float(obtainedData['yPos'])-(car_width/2) >= (left_line_ys[box]+trigger_offset) or (left_line_ys[box]+line_width-trigger_offset) >= (float(obtainedData['yPos'])+(car_width/2)) >= (left_line_ys[box]+trigger_offset) or (left_line_ys[box]+line_width-trigger_offset) <= (float(obtainedData['yPos'])+(car_width/2)) and (float(obtainedData['yPos'])-(car_width/2)) <= (left_line_ys[box]+trigger_offset))):
                                tracked_car = dict(obtainedData)
                                tracked_car['objMessage'] = 'Trigger'
                                tracked_car['objZone'] = box
                                cars.append(tracked_car)

                    incoming_data = incoming_data[:-11]
                else:
                    incoming_data = []
                    write_csv(cars)
                    cars_coming = False
        data = ser.read(1)
        print(data)
        incoming_data.append(binascii.hexlify(data).decode(encoding='UTF-8'))
        if len(incoming_data) >3:
            last_three = (incoming_data[len(incoming_data)-3]+incoming_data[len(incoming_data)-2]+incoming_data[len(incoming_data)-1])
            if (last_three == possible_satus_ids[0] or (last_three == possible_satus_ids[1]) or (last_three == possible_satus_ids[2]) or (last_three == possible_satus_ids[3])):
                cars_coming = True
                status_id_type = incoming_data[len(incoming_data)-3]
                incoming_data = incoming_data[-3:]          
        
else:
    print('port not open')
ser.close()
