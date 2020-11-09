#(C) Copyright 2020 Andy Knitt


import os
import argparse
import sys
import datetime
import time
import json

parser = argparse.ArgumentParser(description='List all TGIDs in a time range of trunk-recorder recordings')
parser.add_argument('Path', help='Path to the base trunk-recorder audio recording directory for the system in question')
parser.add_argument('Date', help='Date of the recordings to retrieve in MM/DD/YYYY format')
parser.add_argument('StartTime', help='Start time of the recordings to retrieve in HH:MM:SS format')
parser.add_argument('StopTime', help='End time of the recordings to retrieve in HH:MM:SS format')

args = parser.parse_args()
rpath = args.Path
rdate = args.Date
ryear = rdate.split('/')[2]
rmonth = str(int(rdate.split('/')[0]))
rday = str(int(rdate.split('/')[1]))
start_time = args.StartTime
stop_time = args.StopTime

#Argument validation#############
#confirm that audio path exists
if not os.path.isdir(rpath):
	print("Error - Path to the base trunk-recorder audio recording directory not found")
	sys.exit()
#Confirm that date folder exists
rfilepath = rpath + "/" + ryear + "/" + rmonth + "/" + rday
if not os.path.isdir(rfilepath):
	print("Error - No recordings found for date provided")
	sys.exit()
#Confirm that StopTime is later than StartTime
#utc_offset = time.gmtime()[3]-time.localtime()[3]
if time.daylight == 0:
	utc_offset = time.timezone
else:
	utc_offset = time.altzone
print utc_offset
start_timestamp = (datetime.datetime(int(ryear),int(rmonth),int(rday),int(start_time.split(':')[0]),int(start_time.split(':')[1]),int(start_time.split(':')[2]))-datetime.datetime(1970,1,1)+datetime.timedelta(seconds=utc_offset)).total_seconds()
stop_timestamp = (datetime.datetime(int(ryear),int(rmonth),int(rday),int(stop_time.split(':')[0]),int(stop_time.split(':')[1]),int(stop_time.split(':')[2]))-datetime.datetime(1970,1,1)+datetime.timedelta(seconds=utc_offset)).total_seconds()
if start_timestamp > stop_timestamp:
	print("Error - start time is greater than stop time")
	sys.exit()

##############################################

fnames = []
min_timestamp = 2**64
TGIDs = []
for fname in os.listdir(rfilepath):
	if fname.endswith(".json"):
		timestamp = int(fname[fname.find("-")+1:fname.find("_")])
		#print(timestamp)
		TGID = fname[0:fname.find("-")]

		if TGID not in TGIDs and timestamp > start_timestamp and timestamp < stop_timestamp:
			TGIDs.append(TGID)

TGIDs.sort()
print(start_timestamp)
print(stop_timestamp)
print(TGIDs)
