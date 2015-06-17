import socket
import cv2
import numpy as np
import sys
import time
import io
import threading
import picamera
from PIL import Image
SERVER = '127.0.0.1' # Server IP or domain
PORT = 10003 # Server port
# Create a pool of image processors
done = False
lock = threading.Lock()
pool = []
buffer = ""
index=0
preamble = False
FRAMERATE=10
PIXELX=181
PIXELY=142
THREADS=1
"""
 This function read a character from a buffer (fd) until it reads 
 the character (until), and return the string.
"""
def read_until(fd, until):
    to_ret = ''
    try:
        a = fd.recv(1)
        while a[0] != until:
            to_ret += a
            a = fd.recv(1)

        to_ret += a
    except:
        print "Error: Socket closed (or another thing!) :P"
        return None
    return to_ret;
def connectar(sock):
    # Connect the socket to the port where the server is listening
    server_address = (SERVER, PORT)
    print 'Connecting to %s in port %s' % server_address
    sock.connect(server_address)
def enviar(mensage, sock):
     try:
        
	    # Wait the response
	    print 'Sending: %s' % mensage
	    sock.sendall(mensage)
	   
     except:
	    print "ERROR"

class ImageProcessor(threading.Thread):
    def __init__(self):
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.start()

    def run(self):
        # This method runs in a separate thread
        global done
	global index
	global preamble
	global buffer
        while not self.terminated:
            # Wait for an image to be written to the stream
	    
	    
            if self.event.wait(1):
                try:
                    self.stream.seek(0)
		    
                    # Read the image and do some processing on it
		  
                    im = Image.open(self.stream)
        	    pixels = im.load()
		    p1 = pixels[PIXELX,PIXELY]
		    if p1[-1]<= 15:
			   
			    if preamble == True:
				buffer+="0"
				index=index+1	
				print repr(index)+": 0"
		    else:
			    
			    
			    if preamble==True:
				buffer+="1"
				index=index+1
				print repr(index)+": 1"
			    else:
				preamble=True
		    if len (buffer)== 13:
		           
		            preamble = False
 			    print "DETECTED: "+buffer			   
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            connectar(sock)			                            
			    enviar(buffer, sock)
			    buffer=""
		         
			
                    # Set done to True if you want the script to terminate
                    # at some point
                    #done=True
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the pool
                    with lock:
                        pool.append(self)
def streams():
    while not done:
        with lock:
            if pool:
                processor = pool.pop()
            else:
                processor = None
        if processor:
            yield processor.stream
            processor.event.set()
        else:
            # When the pool is starved, wait a while for it to refill
            time.sleep(0.1)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# rebem dades i processem
# if( 1 ){ connectem i enviem}
with picamera.PiCamera() as camera:
    pool = [ImageProcessor() for i in range(THREADS)]
    camera.resolution = (320, 240)
    camera.framerate = FRAMERATE
    camera.capture_sequence(streams(), use_video_port=True)

# Shut down the processors in an orderly fashion
while pool:
    with lock:
        processor = pool.pop()
    processor.terminated = True
    processor.join()






        

