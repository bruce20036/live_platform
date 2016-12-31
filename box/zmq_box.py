import sys, os
import zmq
import time



class zmq_PUB_BOX(object):
    def __init__(self, box_id, ip_port):
        self.flag = True
        self.id = box_id
        # Prepare our context and publisher
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(ip_port)

    
    def run(self, topic, ping_sec=3):
        while self.flag:
            self.socket.send_string("%s %s" % (topic, str(self.id)))
            time.sleep(ping_sec)
            
