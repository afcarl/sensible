#!/usr/bin/env bash

RUN_FOR=300
RADAR_COM_PORT="/dev/ttyUSB0"
RADAR_LANE=4
RADAR_ORIENTATION=99.31
# translation to radar (x: 33 m, y: -154 m)
RADAR_LAT="29.6363969"
RADAR_LON="-82.3400241"
DSRC_IP_ADDRESS="169.254.30.4"
DSRC_REMOTE_PORT=4200
ASSOCIATION_THRESHOLD=150
OUTPUT_PORT=24601

python main.py --run-for $RUN_FOR --radar-lane $RADAR_LANE --radar-orientation $RADAR_ORIENTATION --dsrc-ip-address $DSRC_IP_ADDRESS --dsrc-remote-port $DSRC_REMOTE_PORT --association-threshold $ASSOCIATION_THRESHOLD --output-port $OUTPUT_PORT --v --record-csv