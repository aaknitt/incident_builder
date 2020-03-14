#Convert .wav file to .au file for use in Audacity
# 
#Audacity .au format - unofficial
# Essentially a little-endian version of the Sun Microsystems .au format:
#  https://en.wikipedia.org/wiki/Au_file_format
# 
#While the Sun .au format supports both big and little endian, it seems as though Audacity only supports
# little endian.  
#
# ffmpeg can convert to .au format but appears to only do it in big endian, which doesn't seem to work with Audacity
#
# Bytes . . . . . . . . . . . Content
# --------------------------------------------------------------------------------------------------
# 4 . . . . . . . . . . . . . "dns." [exact reverse of .snd, the "magic number" of the Sun Microsystem's .au]
# 4 . . . . . . . . . . . . . Little endian hex Offset to audio data
# 4 . . . . . . . . . . . . . 0xFFFFFFFF [length of data - 0xFFFFFFFF represents 'unknown']
# 4 . . . . . . . . . . . . . 0x06000000 - little endian audio data format specifier per Sun .au spec.  0x06 = 32 bit float
# 4 . . . . . . . . . . . . . Little endian hex version of sampling rate in Hz
# 4 . . . . . . . . . . . . . Little endian hex version of number of interleaved channels 
# 8 . . . . . . . . . . . . . "Audacity"
# 12 . . . . . . . . . . . . "BlockFile112"	 [Why "112"?]	
# Offset - 44 . . . . . . . .Audio summary data - block of min,max,rms values for every 256 audio frames, then another block of min,max,rms values for every 65536 audio frames
# File_size - Offset . . . Audio in  32 bit IEEE-754 floating point
import wave
import struct
import math

def convert_wav_to_au(wavefilein,aufileout,start_sec=0,duration_sec=None):
	wav = wave.open(wavefilein,'rb')
	au = open(aufileout,'wb')
	srate = wav.getframerate()
	sampwidth = wav.getsampwidth()
	nframes = wav.getnframes()

	#print("Sampling Rate = " + str(srate))
	#print("Sampling Width = " + str(sampwidth))
	#print("NumFrames = " + str(nframes))

	audioframes=[]
	previewframes=[]
	previewcount = 0
	preframes = int(start_sec*srate)
	wav.readframes(preframes)  #get to where we want to start reading
	if duration_sec==None:
		readframes = nframes-preframes
	else:
		readframes = int(duration_sec*srate)
	counter256 = 0
	counter64k = 0
	min256 = 0
	max256 = 0
	sumsq256 = 0
	min64k = 0
	max64k = 0
	sumsq64k = 0
	summary256 = []
	summary64k = []
	for k in range(0, readframes):
		frame = wav.readframes(1)  #could probably speed this up quite a bit by reading in 256 frames at a time
		frame = struct.unpack('<h',frame)[0]
		audioframes.append(frame)
		if frame < min256:
			min256 = frame
		if frame > max256:
			max256 = frame
		sumsq256 = sumsq256+frame*frame
		if counter256 == 255:
			summary256.append(min256)
			summary256.append(max256)
			summary256.append(math.sqrt(sumsq256))
			min256 = 0
			max256 = 0
			sumsq256 = 0
			counter256 = 0
		else:
			counter256 = counter256 + 1
		if counter64k == 65535:
			summary64k.append(min64k)
			summary64k.append(max64k)
			summary64k.append(math.sqrt(sumsq64k))
			min64k = 0
			max64k = 0
			sumsq64k = 0
			counter64k = 0
		else:
			counter64k = counter64k + 1
	
		#if k%85 == 0:  #preview data is at 1/85 sample rate
			#THIS ISN'T RIGHT....NEED TO FIGURE OUT HOW TO CORRECTLY CREATE PREVIEW DATA
		#	previewframes.append(frame)
		#	previewcount = previewcount + 4

	au.write("dns.")  #backwards '.snd' from .au file format to specify little-endian
	au.write(struct.pack('<I',0x2C+len(summary256)*4+len(summary64k)*4))  #Data Offset in bytes
	au.write(struct.pack('<I',0xFFFFFFFF))  #Data Size
	au.write(struct.pack('<I',0x06))  #Data encoding format.  6=32 bit IEEE floating point
	au.write(struct.pack('<I',srate))  #sampling rate
	au.write(struct.pack('<I',1))  #number of interleaved audio channels
	au.write("AudacityBlockFile112")  #Audacity-specific string

	#write summary256 data (annotation field)
	for sframe in summary256:
		au.write(struct.pack('<f',sframe/float(2**(sampwidth*8)/2)))
	#write summary64k data (annotation field)
	for sframe in summary64k:
		au.write(struct.pack('<f',sframe/float(2**(sampwidth*8)/2)))
	#write actual audio data
	for aframe in audioframes:
		au.write(struct.pack('<f',aframe/float(2**(sampwidth*8)/2)))
		
	au.close()
	wav.close()

	return readframes, srate