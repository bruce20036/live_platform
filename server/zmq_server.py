import zmq
import time
import redis
import configfile
from server.tasks import logmsg, update_M3U8

def run_zmq_SUB_server(rdb):
    """
    - Redis Data structure
        - box_id (hash): key - box_id
                         fields - "IP", "PORT"
        
        - media_path (hash): key - media_path
                             fields - "IP", "PORT", "CHECK", "SEND_TIME",
                                      "ASSIGN_SERVER"
                         
        - redis_box_set (sorted set): key - redis_box_set
                                      score - int(time.time())
                                      member - box_id
        
        - box_media_load (sorted set): key - redis_box_media_amount
                                       score - holding media amounts
                                       member - box_id
                                       
    - Accept Boxes' maintain topic and  verify topic
    
    """
    # Import variable from configfile
    maintain_topic      = configfile.ZMQ_MT_TOPIC
    verify_topic        = configfile.ZMQ_VERIFY_TOPIC
    redis_box_set       = configfile.REDIS_BOX_SET
    expire_box_time     = configfile.EXPIRE_BOX_TIME
    expire_media_time   = configfile.EXPIRE_MEDIA_TIME 
    redis_box_media_amount = configfile.REDIS_BOX_MEDIA_AMOUNT
    # ZMQ objects establish
    context         = zmq.Context()
    socket          = context.socket(zmq.SUB)
    socket.bind(configfile.ZMQ_MT_SUB_TCP)
    socket.setsockopt_string(zmq.SUBSCRIBE, maintain_topic)
    socket.setsockopt_string(zmq.SUBSCRIBE, verify_topic)
    time.sleep(1)
    # CLEAR ALL KEYS IN REDIS BEFORE START
    for box in rdb.keys("box-*"):
        rdb.delete(box)
    rdb.delete(redis_box_set)
    rdb.delete(redis_box_media_amount)
    while True:
            # Read envelope with address
            string = socket.recv_string()
            topic = string.split(' ', 1)[0]
            if topic == maintain_topic:
                # BOX ID NEEDS TO BE "box-(UUID)"
                topic, box_id, box_ip, box_port, media_amount = string.split(" ")
                if box_id[:4] != 'box-':
                    continue
                if not rdb.exists(box_id):
                    # ADD hash to redis, set box_id as key
                    rdb.hmset(box_id, {"IP":box_ip, "PORT":box_port})
                rdb.zadd(redis_box_set, int(time.time()) + expire_box_time, box_id)
                rdb.zadd(redis_box_media_amount, int(media_amount), box_id)
                logmsg(string)
            elif topic == verify_topic:
                topic, box_id, media_path = string.split(" ")
                if rdb.exists(media_path):
                    box_ip, box_port = rdb.hmget(box_id, "IP", "PORT")
                    if rdb.hmget(media_path, "USE_SERVER")[0] == "True":
                        pre, stream_name, time_segment = media_path.rsplit('/', 2)
                        m3u8_path = pre + "/" + stream_name + "/" + "index.m3u8"
                        update_M3U8.delay(box_ip, box_port, time_segment, m3u8_path)
                        rdb.hmset(media_path, {"USE_SERVER":"False",})
                    rdb.hmset(media_path, {"IP":box_ip, "PORT":box_port, "CHECK":"True"})
                    rdb.expire(media_path, expire_media_time)
                    rdb.zadd(redis_box_set, int(time.time()) + expire_box_time, box_id)
                    send_time = float(rdb.hmget(media_path, "SEND_TIME")[0])
                    logmsg("%s. SEND TIME: %s sec. SERVER -> %s"%(media_path,
                                                                  str(time.time()-send_time),
                                                                  box_id))
    
def expire_box_set_members(rdb):
    redis_box_set = configfile.REDIS_BOX_SET
    redis_box_media_amount = configfile.REDIS_BOX_MEDIA_AMOUNT
    while True:
        expire_box_list = rdb.zrangebyscore(redis_box_set, 0, int(time.time()))
        for box_id in expire_box_list:
            rdb.delete(box_id)
            rdb.zrem(redis_box_set, box_id)
            rdb.zrem(redis_box_media_amount, box_id)
        time.sleep(1)

