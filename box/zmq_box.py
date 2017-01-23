import sys
import os
import zmq
import time
import subprocess
import multiprocessing
import configfile
import logging


def logmsg(msg):
    logging.basicConfig(format='%(asctime)s Message: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.warning(msg)


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
    while 1:
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
    context         = zmq.Context()
    socket          = context.socket(zmq.SUB)
    socket.connect(configfile.ZMQ_XPUB_ADDRESS)
    verify_socket   = context.socket(zmq.PUB)
    verify_socket.connect(configfile.ZMQ_MT_PUB_TCP)
    verify_topic    = configfile.ZMQ_VERIFY_TOPIC
    socket.setsockopt(zmq.SUBSCRIBE, box_id)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    print("run_zmq_MEDIA_BOX start...")
    while 1:
        data = socket.recv_multipart()
        if len(data)<3:
            continue
        verify_socket.send_string("%s %s %s"%(verify_topic, box_id, data[1]))
        logmsg(name+" "+" Get data in MEDIA_PATH: %s"%(data[1]))
        pre_dir, stream_name, media_name = data[1].rsplit("/", 2)
        if "ts" == media_name[-2:]:
            output_folder   = configfile.BOX_MEDIA_WRITE_DIR + "/" + stream_name
            output_path     = output_folder + "/" + media_name
        # Assume MPD
        else:
            output_folder   = configfile.BOX_MEDIA_WRITE_DIR + "/"+stream_name
            output_path     = output_folder+"/"+media_name
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
        rdb.zadd("Expired-"+output_folder, int(time.time()) + expired_time, output_path)


def recycle_expired_boxes(rdb):
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