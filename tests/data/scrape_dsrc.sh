#!/bin/bash 

DSRC_DIR="/Users/pemami/Dropbox (UFL)/Data/SW-42nd-SW-40-Radar-Installation/Vehicle GPS/log/"
DEST_DIR="/Users/pemami/Dropbox (UFL)/Data/SW-42nd-SW-40-Radar-Installation/Cleaned DSRC/"
files=("suilog_1492107714" "suilog_1492107906" "suilog_1492108094" "suilog_1492108311" "suilog_1492108557" "suilog_1492108779" "suilog_1492108956")

for i in "${files[@]}"
do 
    python parse_suitcase_file.py --file "$DSRC_DIR$i.txt" --dest "$DEST_DIR$i"".pkl" 
done
