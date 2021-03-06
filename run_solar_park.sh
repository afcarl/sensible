#!/usr/bin/env bash

# Run for X seconds
RUN_FOR=900

#RADAR_COM_PORT="/dev/ttyUSB0"
#RADAR_LANE=4
#RADAR_ORIENTATION=156.63
#RADAR_LAT="30.4107008"
#RADAR_LON="-84.3050721"
DSRC_IP_ADDRESS="169.254.30.4"
DSRC_REMOTE_PORT=4200
ASSOCIATION_THRESHOLD=150
OUTPUT_PORT=24602

python main.py --disable-radar --run-for $RUN_FOR --dsrc-ip-address $DSRC_IP_ADDRESS --dsrc-remote-port $DSRC_REMOTE_PORT --association-threshold $ASSOCIATION_THRESHOLD --output-port $OUTPUT_PORT --v
