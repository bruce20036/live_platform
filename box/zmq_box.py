import sys
import os
import zmq
import time
import subprocess
import threading
import configfile
from server.tasks import logmsg

class zmq_PUB_BOX(threading.Thread):
    def __init__(self, box_id, ip, port, topic, ping_sec=3):
        
        ### THREADING SETTINGS
        super(zmq_PUB_BOX, self).__init__(name="PUB_BOX THREAD")
        self.stop     = threading.Event()
        self.id       = box_id
        ### IP PORT SHOULD BE WHERE CLIENT's BROWSER TO GET THEIR MEDIAs
        self.ip       = ip
        self.port     = port
        self.topic    = topic
        self.ping_sec = ping_sec
        
        ### Prepare our context and publisher
        self.context  = zmq.Context()
        self.socket   = self.context.socket(zmq.PUB)
        self.socket.bind(configfile.ZMQ_MT_PUB_TCP)

    def run(self):
        print self.getName()+"start..."
        while not self.stop.is_set():
            msg = "%s %s %s %s" % (self.topic, str(self.id), self.ip, self.port)
            self.socket.send_string(msg)
            logmsg(self.getName()+msg)
            time.sleep(self.ping_sec)
    
    def stop(self):
        self.stop.set()


class zmq_MEDIA_BOX(threading.Thread):
    def __init__(self, box_id, ip, port):
        ### THREADING SETTINGS
        super(zmq_MEDIA_BOX, self).__init__(name="MEDIA_BOX THREAD")
        self.stop = threading.Event()
        self.id = box_id
        
        ###ZMQ SETTINGS        
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.bind("tcp://"+ip+":"+port)
        self.socket.setsockopt(zmq.SUBSCRIBE, str(box_id))
        time.sleep(0.05)
 
    def run(self):
        print self.getName()+"start..."
        while not self.stop.is_set():
            ### data = [TOPIC, MEDIA_PATH, media_file......]
            data = self.socket.recv_multipart()
            logmsg(self.getName()+" Get data in TOPIC: %s MEDIA_PATH: %s"%(data[0], data[1]))
            
            if len(data)<3:
                continue

            pre_dir, stream_name, media_name = data[1].rsplit("/", 2)
            ### MAKE SURE THAT DIRECTORY OF MPD SHOULD EXIST
            output_folder = configfile.MEDIA_OUTPUT_FOLDER+"/"+stream_name
            output_path = output_folder+"/"+media_name
            if not os.path.isdir(output_folder):
                subprocess.check_output(['mkdir', '-p', output_folder])
            outfile = open(output_path, "wb")
            
            ###START TO WRITE DATA
            for item in data[2:]:
                outfile.write(item)
                outfile.flush()
            outfile.close()

    def stop(self):
        self.stop.set()
 
        
        
    
            
