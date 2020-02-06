from wavtoau import convert_wav_to_au
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os

fname_base = 'test'
if not os.path.isdir(fname_base + '_data'):
	os.mkdir(fname_base + '_data')
nsamples, srate = convert_wav_to_au('test.wav',fname_base + '_data\\test.au',2,1)
print nsamples


# create the AUP XML file structure
data = ET.Element('project')
data.set('xmlns','http://audacity.sourceforge.net/xml')
data.set('projname',fname_base + '_data')
data.set('version','1.3.0')
data.set('audacityversion','2.0.6')
data.set('rate',str(srate))
tags = ET.SubElement(data,'tags')
#CREATE A NEW WAV TRACK FOR EACH TGID
wavetrack = ET.SubElement(data, 'wavetrack')
wavetrack.set('name','Audio Track')
wavetrack.set('channel','2')  #increment this for each track
wavetrack.set('linked','0')
wavetrack.set('mute','0')
wavetrack.set('solo','0')
wavetrack.set('height','150')
wavetrack.set('minimized','0')
wavetrack.set('rate',str(srate))
wavetrack.set('gain','1')
wavetrack.set('pan','0')
#CREATE A NEW WAVCLIP FOR EACH TRANSMISSION IN THE TGID(MAY BE MORE THAN ONE TRANSMISSION PER WAV - BASED ON JSON)
waveclip = ET.SubElement(wavetrack, 'waveclip')
waveclip.set('offset','0')
envelope = ET.SubElement(waveclip,'envelope')
envelope.set('numpoints','0')
sequence = ET.SubElement(waveclip,'sequence')
sequence.set('maxsamples',str(nsamples))
sequence.set('sampleformat','262159')
sequence.set('numsamples',str(nsamples))
waveblock = ET.SubElement(sequence,'waveblock')
waveblock.set('start','0')
simpleblockfile = ET.SubElement(waveblock,'simpleblockfile')
simpleblockfile.set('filename',fname_base + '.au')
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