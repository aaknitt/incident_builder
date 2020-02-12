#(C) Copyright 2020 Andy Knitt


from wavtoau import convert_wav_to_au
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import argparse
import sys
import datetime
import time
import json

parser = argparse.ArgumentParser(description='Build an Audicity multi-track project from multiple talkgroups in trunk-recorder recordings')
parser.add_argument('Path', help='Path to the base trunk-recorder audio recording directory for the system in question')
parser.add_argument('Date', help='Date of the recordings to retrieve in MM/DD/YYYY format')
parser.add_argument('StartTime', help='Start time of the recordings to retrieve in HH:MM:SS format')
parser.add_argument('StopTime', help='End time of the recordings to retrieve in HH:MM:SS format')
parser.add_argument('TGIDS', help='Comma separated list of decimanl format talkgroup IDs to retreive')
parser.add_argument('OutFile', help='Filename of the output Audacity project file.  Must end with .aup extension')
parser.add_argument('--splitwav', dest='splitwav', action='store_true', help='When set, split WAV files into multiple segments in the Audacity track based on the logged JSON data. Results in more accurate timing of reconstructed audio.  Default is set.')
parser.add_argument('--no-splitwav',dest='splitwav', action='store_false', help='When set, a single segment is created in Audacity per WAV file.  Default is to use --splitwav')
parser.set_defaults(splitwav=True)

args = parser.parse_args()
rpath = args.Path
rdate = args.Date
ryear = rdate.split('/')[2]
rmonth = str(int(rdate.split('/')[0]))
rday = str(int(rdate.split('/')[1]))
start_time = args.StartTime
stop_time = args.StopTime
TGIDS = args.TGIDS.split(',')
outfile = args.OutFile
splitwav = args.splitwav

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
utc_offset = time.timezone
print utc_offset
start_timestamp = (datetime.datetime(int(ryear),int(rmonth),int(rday),int(start_time.split(':')[0]),int(start_time.split(':')[1]),int(start_time.split(':')[2]))-datetime.datetime(1970,1,1)+datetime.timedelta(seconds=utc_offset)).total_seconds()
stop_timestamp = (datetime.datetime(int(ryear),int(rmonth),int(rday),int(stop_time.split(':')[0]),int(stop_time.split(':')[1]),int(stop_time.split(':')[2]))-datetime.datetime(1970,1,1)+datetime.timedelta(seconds=utc_offset)).total_seconds()
if start_timestamp > stop_timestamp:
	print("Error - start time is greater than stop time")
	sys.exit()
#Confirm that Outfile ends with .aup
if outfile[-4:] != '.aup':
	print("Error - invalid output filename - must end in .aup")
	sys.exit()
##############################################

datadir = outfile.replace('.aup','') + '_data'  #Audacity requires data directory to have this naming convention
if not os.path.isdir(datadir):
	os.mkdir(datadir)

fnames = []
min_timestamp = 2**64
for fname in os.listdir(rfilepath):
	if fname.endswith(".json"):
		timestamp = int(fname[fname.find("-")+1:fname.find("_")])
		#print(timestamp)
		TGID = fname[0:fname.find("-")]
		#print(TGID)
		if TGID in TGIDS and timestamp > start_timestamp and timestamp < stop_timestamp:
			fnames.append(fname)
			if timestamp < min_timestamp:
				min_timestamp = timestamp
fnames.sort()
print(start_timestamp)
print(stop_timestamp)
print(min_timestamp)
print(TGIDS)
# create the AUP XML file structure
data = ET.Element('project')
data.set('xmlns','http://audacity.sourceforge.net/xml')
data.set('projname',outfile.replace('.aup','') + '_data')
data.set('version','1.3.0')
data.set('audacityversion','2.0.6')
data.set('rate','8000')
tags = ET.SubElement(data,'tags')
#CREATE A NEW WAV TRACK FOR EACH TGID
for TGID in TGIDS:
	wavetrack = ET.SubElement(data, 'wavetrack')
	wavetrack.set('name','TG' + str(TGID))
	wavetrack.set('channel','2')  #0 = Left, 1 = Right, 2 = Mono
	wavetrack.set('linked','0')
	wavetrack.set('mute','0')
	wavetrack.set('solo','0')
	wavetrack.set('height','100')
	wavetrack.set('minimized','0')
	wavetrack.set('rate','8000')
	wavetrack.set('gain','1')
	wavetrack.set('pan','0')
	#CREATE A NEW WAVCLIP FOR EACH TRANSMISSION IN THE TGID(MAY BE MORE THAN ONE TRANSMISSION PER WAV - BASED ON JSON)
	for fname in fnames:
		timestamp = int(fname[fname.find("-")+1:fname.find("_")])
		if fname[0:fname.find("-")] == TGID:
			wavefilename = rfilepath + "/" + fname.replace('json','wav')
			print(wavefilename)
			with open(rfilepath + "/" + fname) as json_file:
					jdata = json.load(json_file)
			if args.splitwav == True and len(jdata['srcList']) > 1:
				i = 0
				#CREATE A FOR LOOP WITH THE NUMBER OF SEGMENTS IN THE WAV, INCREMENT .AU FILENAME EACH TIME
				srcList = jdata['srcList']
				for n, src in enumerate(srcList):
					pos = float(src['pos'])
					timestamp = int(src['time'])
					aufilename = fname.replace('.json','') + str(i) + '.au'
					i = i + 1
					if n == len(srcList)-1:
						nsamples, srate = convert_wav_to_au(wavefilename,datadir + '/' + aufilename,pos,None)
					else:
						nsamples, srate = convert_wav_to_au(wavefilename,datadir + '/' + aufilename,pos,float(srcList[n+1]['pos'])-pos)
					if nsamples <=0:
						os.remove(datadir + '/' +aufilename)
					else:
						waveclip = ET.SubElement(wavetrack, 'waveclip')
						offset = timestamp - min_timestamp
						waveclip.set('offset',str(offset))
						envelope = ET.SubElement(waveclip,'envelope')
						envelope.set('numpoints','0')
						sequence = ET.SubElement(waveclip,'sequence')
						sequence.set('maxsamples',str(nsamples))
						sequence.set('sampleformat','262159')
						sequence.set('numsamples',str(nsamples))
						waveblock = ET.SubElement(sequence,'waveblock')
						waveblock.set('start','0')
						simpleblockfile = ET.SubElement(waveblock,'simpleblockfile')
						simpleblockfile.set('filename',aufilename)
						simpleblockfile.set('len',str(nsamples))
			else:
				aufilename = fname.replace('.json','') + '.au'
				nsamples, srate = convert_wav_to_au(wavefilename,datadir + '/' + aufilename,0,None)
				waveclip = ET.SubElement(wavetrack, 'waveclip')
				offset = timestamp - min_timestamp
				waveclip.set('offset',str(offset))
				envelope = ET.SubElement(waveclip,'envelope')
				envelope.set('numpoints','0')
				sequence = ET.SubElement(waveclip,'sequence')
				sequence.set('maxsamples',str(nsamples))
				sequence.set('sampleformat','262159')
				sequence.set('numsamples',str(nsamples))
				waveblock = ET.SubElement(sequence,'waveblock')
				waveblock.set('start','0')
				simpleblockfile = ET.SubElement(waveblock,'simpleblockfile')
				simpleblockfile.set('filename',aufilename)
				simpleblockfile.set('len',str(nsamples))
				
# create a new AUP XML file with the results
mydata = ET.tostring(data)
dom = xml.dom.minidom.parseString(mydata) # or xml.dom.minidom.parseString(xml_string)
pretty_xml_as_string = dom.toprettyxml()
myfile = open(outfile, "w")
myfile.write(pretty_xml_as_string)
myfile.close()