import zmq
import time
from .. import settings

class zmq_SUB_server(object):
    def __init__(self, ip_port, topic):
        self.flag = True
        # Prepare our context and socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(ip_port)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        
        
    def run(self):
        while self.flag:
            # Read envelope with address
            string = socket.recv_string()
            topic, box_id = string.split(" ")

