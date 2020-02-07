from wavtoau import convert_wav_to_au
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os

fname_base = 'test'
if not os.path.isdir(fname_base + '_data'):
	os.mkdir(fname_base + '_data')


fnames = []
TGIDS = []
min_timestamp = 2**64
for fname in os.listdir("sample_data"):
	if fname.endswith(".json"):
		fnames.append(fname)
		TGID = fname[0:fname.find("-")]
		if TGID not in TGIDS:
			TGIDS.append(TGID)
		timestamp = int(fname[fname.find("-")+1:fname.find("_")])
		if timestamp < min_timestamp:
			min_timestamp = timestamp
			
print TGIDS
print fnames
print min_timestamp
		

# create the AUP XML file structure
data = ET.Element('project')
data.set('xmlns','http://audacity.sourceforge.net/xml')
data.set('projname',fname_base + '_data')
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
		if fname[0:fname.find("-")] == TGID:
			wavefilename = 'sample_data\\' + fname.replace('json','wav')
			print wavefilename
			#HERE IS WHERE WE NEED TO FIGURE OUT IF WE NEED TO SPLIT THE WAV BY LOOKING AT JSON
			#CREATE A FOR LOOP WITH THE NUMBER OF SEGMENTS IN THE WAV, INCREMENT .AU FILENAME EACH TIME
			#MAKE THIS A CONFIGURATION PARAMETER - SPLIT OR DON'T SPLIT WAV FILES BY COMMAND LINE FLAG
			aufilename = fname.replace('.json','') + str(i) + '.au'
			nsamples, srate = convert_wav_to_au(wavefilename,fname_base + '_data\\' + aufilename,0,None)
			#print srate
			#print nsamples
			waveclip = ET.SubElement(wavetrack, 'waveclip')
			timestamp = int(fname[fname.find("-")+1:fname.find("_")])
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
			simpleblockfile.set('min',"-1")
			simpleblockfile.set('max','1')
			simpleblockfile.set('rms','.2')



# create a new AUP XML file with the results
mydata = ET.tostring(data)
dom = xml.dom.minidom.parseString(mydata) # or xml.dom.minidom.parseString(xml_string)
pretty_xml_as_string = dom.toprettyxml()
myfile = open(fname_base + ".aup", "w")
myfile.write(pretty_xml_as_string)
myfile.close()