import zmq
import time
import redis
import configfile

class zmq_SUB_server(object):
    def __init__(self):
        self.flag = True
        # Prepare our context and socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(configfile.ZMQ_MT_SUB_TCP)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, configfile.ZMQ_MT_TOPIC)
        self.redis = redis.StrictRedis()        
        
    def run(self, expire_time=4):
        while self.flag:
            # Read envelope with address
            string = self.socket.recv_string()
            print string
            #BOX ID NEEDS TO BE "box-(UUID)"
            topic, box_id, box_ip, box_port = string.split(" ")
            #ADD hash to redis, set box_id as key
            self.redis.hmset(box_id, {"IP":box_port, "PORT":box_port,})
            #expire key after 4 sec as default (box ping every 3 sec)
            self.redis.expire(box_id, expire_time)



            

