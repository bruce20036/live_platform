import zmq
import time
import redis
import configfile
from server.tasks import logmsg

def run_zmq_SUB_server():
    context = zmq.Context()
    socket  = context.socket(zmq.SUB)
    socket.bind(configfile.ZMQ_MT_SUB_TCP)
    socket.setsockopt_string(zmq.SUBSCRIBE, configfile.ZMQ_MT_TOPIC)
    rdb     = redis.StrictRedis()
    while True:
            # Read envelope with address
            string = socket.recv_string()
            logmsg(string)
            # BOX ID NEEDS TO BE "box-(UUID)"
            topic, box_id, box_ip, box_port = string.split(" ")
            # ADD hash to redis, set box_id as key
            rdb.hmset(box_id, {"IP":box_ip, "PORT":box_port,})
            # Expire key after 4 sec as default (box ping every 3 sec)
            rdb.expire(box_id, configfile.ZMQ_MT_SERVER_EXPIRE_SEC)
    