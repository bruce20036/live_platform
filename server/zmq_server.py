import zmq
import time
import redis
import configfile
from server.tasks import logmsg

class zmq_SUB_server(object):
    def __init__(self):
        self.flag = True
        # Prepare our context and socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.bind(configfile.ZMQ_MT_SUB_TCP)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, configfile.ZMQ_MT_TOPIC)
        self.redis = redis.StrictRedis()        
        
    def run(self):
        print("zmq_SUB_server start...")
        while self.flag:
            # Read envelope with address
            string = self.socket.recv_string()
            logmsg(string)
            # BOX ID NEEDS TO BE "box-(UUID)"
            
            topic, box_id, box_ip, box_port = string.split(" ")
            # ADD hash to redis, set box_id as key
            self.redis.hmset(box_id, {"IP":box_ip, "PORT":box_port,})
            # Expire key after 4 sec as default (box ping every 3 sec)
            self.redis.expire(box_id, configfile.ZMQ_MT_SERVER_EXPIRE_SEC)


def zmq_PROXY_server():
    context     = zmq.Context()
    socket_sub  = context.socket(zmq.SUB)
    socket_pub  = context.socket(zmq.PUB)
    socket_sub.bind(configfile.ZMQ_XSUB_ADDRESS)
    socket_sub.setsockopt(zmq.SUBSCRIBE, '')
    socket_pub.bind(configfile.ZMQ_XPUB_ADDRESS)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    print("zmq_PROXY_server start...")
    while True:
        data = socket_sub.recv_multipart()
        socket_pub.send_multipart(data)

