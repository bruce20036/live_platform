import sys
import os
import zmq
import time
import subprocess
import multiprocessing
import configfile
import logging
from server.tasks import logmsg


def run_zmq_PUB_BOX(box_id, ip, port, rdb):
    """
    - Connect to zmq as publisher
    - Send a message to server in order to update status
    """
    name     = multiprocessing.current_process().name
    topic    = configfile.ZMQ_MT_TOPIC
    ping_sec = configfile.ZMQ_MT_BOX_UPDATE_SEC
    
    #ZMQ SETTINGS
    context  = zmq.Context()
    socket   = context.socket(zmq.PUB)
    socket.connect(configfile.ZMQ_MT_PUB_TCP)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    print("run_zmq_PUB_BOX start...")
    while True:
        media_amount = 0
        for item in rdb.keys("Expired-*"):
            media_amount += rdb.zcard(item)
        msg = "%s %s %s %s %s" % (topic, str(box_id), ip, port, str(media_amount))
        socket.send_string(msg)
        logmsg(name+" "+msg)
        time.sleep(ping_sec)
        
        
def run_zmq_MEDIA_BOX(box_id, ip, port, rdb):
    """
    - Bind to IP PORT as subscriber in zmq
    - Receive message from server and write file
    """
    name            = multiprocessing.current_process().name
    expired_time    = configfile.BOX_EXPIRE_MEDIA_TIME
    update_duration = configfile.MEDIA_BOX_UDPATE_DURATION
    context         = zmq.Context()
    socket          = context.socket(zmq.SUB)
    socket.connect(configfile.ZMQ_XPUB_ADDRESS)
    verify_socket   = context.socket(zmq.PUB)
    verify_socket.connect(configfile.ZMQ_MT_PUB_TCP)
    verify_topic    = configfile.ZMQ_VERIFY_TOPIC
    socket.setsockopt(zmq.SUBSCRIBE, box_id)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    update_time = time.time()
    current_time = time.time()
    logmsg("%s run_zmq_MEDIA_BOX start..."%(name))
    while time.time() - update_time <= update_duration:
        data = []
        try:
            data = socket.recv_multipart(zmq.NOBLOCK)
        except zmq.ZMQError, e:
            if e.errno == zmq.EAGAIN:
                pass
        if len(data)<3 and data:
            if data[1] == "Update":
                update_time = time.time()
                logmsg("%s: GET MEDIA BOX UPDATE FROM SERVER"%(name))
            else:
                continue
        else:
            continue
        verify_socket.send_string("%s %s %s"%(verify_topic, box_id, data[1]))
        logmsg("%s: Get data in MEDIA_PATH: %s"%(name, data[1]))
        pre_dir, stream_name, media_name = data[1].rsplit("/", 2)
        if "ts" == media_name[-2:]:
            output_folder   = configfile.BOX_MEDIA_WRITE_DIR + "/" + stream_name
            output_path     = output_folder + "/" + media_name
        if rdb.zrank("Expired-"+output_folder, output_path):
            continue
        if not os.path.isdir(output_folder):
            subprocess.check_output(['mkdir', '-p', output_folder])
        outfile = open(output_path, "wb")
        # START TO WRITE DATA
        for item in data[2:]:
            outfile.write(item)
            outfile.flush()
        outfile.close()
        rdb.zadd("Expired-"+ output_folder, int(time.time()) + expired_time, output_path)
    socket.close()
    verify_socket.close()
    context.term()
    logmsg("%s stops."%(name))

def recycle_expired_boxes(rdb):
    print "Recycle Process Start..."
    while True:
        time.sleep(3)
        stream_list = rdb.keys("Expired-"+"/tmp/*")
        if len(stream_list) == 0:
            continue
        for stream in stream_list:
            media_set = rdb.zrangebyscore(stream, 0, int(time.time()))
            for media in media_set:
                try:
                    os.remove(media)
                    rdb.zrem(stream, media)
                except:
                    pass
            rdb.expire(stream, 200)