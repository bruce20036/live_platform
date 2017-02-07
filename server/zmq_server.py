import zmq
import time
import redis
import configfile
import random
import os
from multiprocessing import Process
from server.tasks import logmsg, logwarning, update_M3U8, send_media_box_update,\
                         box_generator, assign_media_to_box

"""
- Redis Data structure
    - box_id (hash): key - box_id
                     fields - "IP", "PORT"
    
    - media_path (hash): key - media_path
                         fields - "BOX_ID", "IP", "PORT", "CHECK", "SEND_TIME",
                                  "ASSIGN_SERVER"
                     
    - redis_box_set (sorted set): key - redis_box_set
                                  score - int(time.time())
                                  member - box_id
    
    - box_media_load (sorted set): key - redis_box_media_amount
                                   score - holding media amounts
                                   member - box_id
                                   
    - box's holding media(strings): key - "Media-"+ box_id +
                                           str(random.randint(0, 99999999999))
                                    value - media_path
                                   
- Accept Boxes' maintain topic and  verify topic
"""


def process_maintain_topic(rdb, redis_box_set, redis_box_media_amount,
                           expire_box_time, string):
    # BOX ID NEEDS TO BE "box-(UUID)"
    topic, box_id, box_ip, box_port, media_amount = string.split(" ")
    if box_id[:4] != 'box-':
        return
    if not rdb.exists(box_id):
        # ADD hash to redis, set box_id as key
        rdb.hmset(box_id, {"IP":box_ip, "PORT":box_port})
    rdb.zadd(redis_box_set, int(time.time()) + expire_box_time, box_id)
    rdb.zadd(redis_box_media_amount, int(media_amount), box_id)
    logmsg(string)

def process_verify_topic(rdb, redis_box_set, expire_box_time, expire_media_time, string):
    topic, box_id, media_path = string.split(" ")
    if rdb.exists(media_path):
        box_ip, box_port = rdb.hmget(box_id, "IP", "PORT")
        rdb.hmset(media_path, {"IP":box_ip, "PORT":box_port, "CHECK":"True"})
        if rdb.hmget(media_path, "ASSIGN_SERVER")[0] == "True":
            pre, stream_name, time_segment = media_path.rsplit('/', 2)
            m3u8_path = configfile.M3U8_WRITE_DIR + "/" + stream_name + "/" + "index.m3u8"
            update_M3U8.delay(box_ip, box_port, stream_name, time_segment, m3u8_path)
            rdb.hmset(media_path, {"ASSIGN_SERVER":"False",})
            logmsg("UPDATE %s WITH %s IN %s"%(media_path, box_id, m3u8_path))
        rdb.expire(media_path, expire_media_time)
        rdb.zadd(redis_box_set, int(time.time()) + expire_box_time, box_id)
        random.seed(int(time.time()))
        box_media_key = "Media-"+ box_id + str(random.randint(0, 99999999999))
        rdb.set(box_media_key, media_path)
        rdb.expire(box_media_key, expire_media_time)
        send_time = rdb.hmget(media_path, "SEND_TIME")[0]
        logmsg("VERIFY MEDIA PATH: %s.\n SERVER ==> %s IP:%s PORT:%s.\n SEND TIME: %s sec."
               %(media_path, box_id, box_ip, box_port, str(time.time()-float(send_time))))


def run_zmq_SUB_server(rdb):
    # Import variable from configfile
    maintain_topic          = configfile.ZMQ_MT_TOPIC
    verify_topic            = configfile.ZMQ_VERIFY_TOPIC
    redis_box_set           = configfile.REDIS_BOX_SET
    expire_box_time         = configfile.EXPIRE_BOX_TIME
    expire_media_time       = configfile.EXPIRE_MEDIA_TIME 
    redis_box_media_amount  = configfile.REDIS_BOX_MEDIA_AMOUNT
    media_box_update_duration = configfile.MEDIA_BOX_UDPATE_DURATION
    # ZMQ objects establish
    context     = zmq.Context()
    socket      = context.socket(zmq.SUB)
    socket.bind(configfile.ZMQ_MT_SUB_TCP)
    socket.setsockopt_string(zmq.SUBSCRIBE, maintain_topic)
    socket.setsockopt_string(zmq.SUBSCRIBE, verify_topic)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    last_media_update_time = time.time()
    # CLEAR ALL KEYS IN REDIS BEFORE START
    for box in rdb.keys("box-*"):
        rdb.delete(box)
    rdb.delete(redis_box_set)
    rdb.delete(redis_box_media_amount)
    logmsg("Server running...")
    while True:
            current_time = time.time()
            if current_time - last_media_update_time >= media_box_update_duration/3:
                send_media_box_update.delay()
                last_media_update_time = time.time()
            string = ''
            try:
                # Read envelope with address
                string = socket.recv_string(zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == zmq.EAGAIN:
                    pass
            if not string: continue
            topic = string.split(' ', 1)[0]
            if topic == maintain_topic:
                process_maintain_topic(rdb, redis_box_set, redis_box_media_amount,
                                        expire_box_time, string)
            elif topic == verify_topic:
                process_verify_topic(rdb, redis_box_set, expire_box_time,
                                     expire_media_time, string)
            
                
def expire_box_set_members(rdb):
    redis_box_set = configfile.REDIS_BOX_SET
    redis_box_media_amount = configfile.REDIS_BOX_MEDIA_AMOUNT
    while True:
        expire_box_list = rdb.zrangebyscore(redis_box_set, 0, int(time.time()))
        for box_id in expire_box_list:
            rdb.delete(box_id)
            substitute_server_for_box(rdb, box_id)
            rdb.zrem(redis_box_set, box_id)
            rdb.zrem(redis_box_media_amount, box_id)
        time.sleep(1)


def substitute_server_for_box(rdb, box_id):
    IP                  = configfile.SERVER_IP
    PORT                = configfile.SERVER_PORT
    M3U8_WRITE_DIR      = configfile.M3U8_WRITE_DIR
    for box_media in rdb.keys("Media-"+box_id+"*"):
        media_path = rdb.get(box_media)
        logmsg("DELETE %s %s"%(box_id, media_path))
        pre, stream_name, time_segment = media_path.rsplit('/', 2)
        m3u8_path = M3U8_WRITE_DIR + "/" + stream_name + "/" + "index.m3u8"
        update_M3U8.delay(IP, PORT, stream_name, time_segment, m3u8_path)
    rdb.delete("Media-"+box_id)

def media_sending_process(rdb):
    """
        Send media to boxes via proxy server
    """
    SEND_MEDIA_QUEUE_NAME   = configfile.SEND_MEDIA_QUEUE_NAME
    m3u8_media_amount       = configfile.M3U8_MEDIA_AMOUNT
    expire_media_time       = configfile.EXPIRE_MEDIA_TIME

    context = zmq.Context()
    socket  = context.socket(zmq.PUB)
    socket.connect(configfile.ZMQ_XSUB_ADDRESS)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    rdb.delete(SEND_MEDIA_QUEUE_NAME)
    
    while True:
        media_path = rdb.lpop(SEND_MEDIA_QUEUE_NAME)
        if not media_path: continue
        media_path = str(media_path)
        if not os.path.isfile(media_path):
            logwarning("send_media_to_box: %s file not found"%(media_path))
            continue
        if not rdb.exists(media_path): continue
        box_id = rdb.hmget(media_path, "BOX_ID")[0]
        if not box_id:
            generator = box_generator(rdb, m3u8_media_amount)
            assign_media_to_box(rdb, generator, expire_media_time, media_path)
            box_id = rdb.hmget(media_path, "BOX_ID")[0]
        box_id = str(box_id)    
        try:
            infile = open(media_path, "rb")
        except:
            logwarning("send_media_to_box can't open %s" % (media_path))
            continue
        # Use BOX_ID as TOPIC
        data = [box_id, media_path]
        data.append(infile.read())
        rdb.hmset(media_path, {"SEND_TIME":str(time.time())})
        # Send data
        socket.send_multipart(data)
        infile.close()
        logmsg("SEND %s TO %s"%(media_path, box_id))

    
    
    