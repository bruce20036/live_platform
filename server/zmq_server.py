import zmq
import time
import redis
import configfile
from server.tasks import logmsg

def run_zmq_SUB_server():
    maintain_topic  = configfile.ZMQ_MT_TOPIC
    verify_topic    = configfile.ZMQ_VERIFY_TOPIC
    context         = zmq.Context()
    socket          = context.socket(zmq.SUB)
    socket.bind(configfile.ZMQ_MT_SUB_TCP)
    socket.setsockopt_string(zmq.SUBSCRIBE, maintain_topic)
    socket.setsockopt_string(zmq.SUBSCRIBE, verify_topic)
    rdb     = redis.StrictRedis()
    time.sleep(1)
    while True:
            # Read envelope with address
            string = socket.recv_string()
            logmsg(string)
            topic = string.split(' ', 1)[0]
            if topic == maintain_topic:
                # BOX ID NEEDS TO BE "box-(UUID)"
                topic, box_id, box_ip, box_port = string.split(" ")
                # ADD hash to redis, set box_id as key
                rdb.hmset(box_id, {"IP":box_ip, "PORT":box_port,})
                # Expire key after 4 sec as default (box ping every 3 sec)
                rdb.expire(box_id, configfile.ZMQ_MT_SERVER_EXPIRE_SEC)
            elif topic == verify_topic:
                topic, box_id, media_path = string.split(" ")
                if rdb.exists(media_path):
                    box_ip, box_port = rdb.hmget(box_id, "IP", "PORT")
                    rdb.hmset(media_path, {"IP":box_ip, "PORT":box_port, "CHECK":"True"})
                    rdb.expire(media_path, 60)
    