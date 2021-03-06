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
		totalframes = nframes-preframes
	else:
		totalframes = int(duration_sec*srate)
	counter64k = 0
	min256 = 0
	max256 = 0
	rms256 = 0
	summary256 = []
	summary64k = []
	min256s = []
	max256s = []
	rms256s = []
	frames_read = 0
	for k in range(0,(totalframes+255)/256):  #read 256 frames at a time to help create summary data while reading frames
		frames_to_read = min(256,totalframes-frames_read)  #read less than 256 frames if we're at the end of the file
		frame = wav.readframes(frames_to_read)
		if sampwidth == 1:
			frame = list(struct.unpack('<' + 'b'*frames_to_read,frame))
		if sampwidth == 2:
			frame = list(struct.unpack('<' + 'h'*frames_to_read,frame))
		if sampwidth == 4:
			frame = list(struct.unpack('<' + 'i'*frames_to_read,frame))
		frames_read = frames_read + frames_to_read  #increment the number of audio frames that we've read so far
		audioframes = audioframes + frame  #add the audio we just read to our list
		min256 = min(frame)    #for summary256 data
		min256s.append(min256) #save to create summary64k data
		max256 = max(frame)    #for summary256 data
		max256s.append(min256) #save to create summary64k data
		rms256 = math.sqrt(sum([i**2 for i in frame]))    #for summary256 data
		rms256s.append(rms256) #save to create summary64k data
		summary256.append(min256)
		summary256.append(max256)
		summary256.append(rms256)
		if counter64k == 255:  #create new entry for summary64k data
			summary64k.append(min(min256s))
			summary64k.append(max(max256s))
			summary64k.append(math.sqrt(sum([i**2 for i in rms256s])))
			min256s = []
			max256s = []
			rms256s = []
			counter64k = 0

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

	return totalframes, srate
