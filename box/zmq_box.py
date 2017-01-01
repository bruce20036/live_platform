import sys, os
import zmq
import time, subprocess
import threading
import configfile

class zmq_PUB_BOX(threading.Thread):
    def __init__(self, box_id, ip, port):
        
        ### THREADING SETTINGS
        super(zmq_PUB_BOX, self).__init__(name="PUB_BOX THREAD")
        self.stop = threading.Event()
        
        self.id = box_id
        ### IP PORT SHOULD BE WHERE CLIENT's BROWSER TO GET THEIR MEDIAs
        self.ip = ip
        self.port = port
        
        ### Prepare our context and publisher
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(configfile.ZMQ_MT_PUB_TCP)

    def run(self, topic, ping_sec=3):
        print self.getName()+"start..."
        while not self.stop.is_set():
            msg = "%s %s %s %s" % (topic, str(self.id), self.ip, self.port)
            self.socket.send_string(msg)
            print self.getName()+msg
            time.sleep(ping_sec)
    
    def stop(self):
        self.stop.set()


class zmq_MEDIA_BOX(threading.Thread):
    def __init__(self, box_id):
        ### THREADING SETTINGS
        super(zmq_MEDIA_BOX, self).__init__(name="MEDIA_BOX THREAD")
        self.stop = threading.Event()
        self.id = box_id
        
        ###ZMQ SETTINGS        
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        print(configfile.ZMQ_MEDIA_DISTRIBUTE_SUB_TCP)
        self.socket.connect(configfile.ZMQ_MEDIA_DISTRIBUTE_SUB_TCP)
        self.socket.setsockopt(zmq.SUBSCRIBE, str(box_id))
        sys.stdout.write(self.getName())
        
    def run(self):
        print self.getName()+"start..."
        while not self.stop.is_set():
            ### data = [TOPIC, MEDIA_PATH, media_file......]
            data = self.socket.recv_multipart()
            print self.getName()+"Get data in TOPIC: %s MEDIA_PATH: %s"%(data[0], data[1])
            
            ### MAKE SURE THAT DIRECTORY OF MPD SHOULD EXIST
            output_folder = data[1].rsplit("/", 1)[0]
            if not os.path.isdir(output_folder):
                subprocess.check_output(['mkdir', '-p', output_folder])
            outfile = open(data[1], "wb")
            
            ###START TO WRITE DATA
            for item in data[2:]:
                outfile.write(item)
                outfile.flush()
            outfile.close()

    def stop(self):
        self.stop.set()
        
        
    
            
