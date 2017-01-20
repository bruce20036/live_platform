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


def run_zmq_PUB_BOX(box_id, ip, port):
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
        msg = "%s %s %s %s" % (topic, str(box_id), ip, port)
        socket.send_string(msg)
        logmsg(name+" "+msg)
        time.sleep(ping_sec)
        
        

def run_zmq_MEDIA_BOX(box_id, ip, port):
    """
    - Bind to IP PORT as subscriber in zmq
    - Receive message from server and write file
    """
    name        = multiprocessing.current_process().name
    context     = zmq.Context()
    socket      = context.socket(zmq.SUB)
    socket.connect(configfile.ZMQ_XPUB_ADDRESS)
    socket.setsockopt(zmq.SUBSCRIBE, box_id)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    print("run_zmq_MEDIA_BOX start...")
    while 1:
        data = socket.recv_multipart()
        if len(data)<3:
            continue
        pre_dir, stream_name, media_name = data[1].rsplit("/", 2)

        if "ts" == media_name[-2:]:
            output_folder   = configfile.M3U8_WRITE_DIR + "/" + stream_name
            output_path     = output_folder + "/" + media_name
        # Assume MPD
        else:
            output_folder   = configfile.MPD_WRITE_DIR+"/"+stream_name
            output_path     = output_folder+"/"+media_name
        if not os.path.isdir(output_folder):
            subprocess.check_output(['mkdir', '-p', output_folder])
        outfile = open(output_path, "wb")
        # START TO WRITE DATA
        for item in data[2:]:
            outfile.write(item)
            outfile.flush()
        outfile.close()
        logmsg(name+" "+" Get data in TOPIC: %s MEDIA_PATH: %s"%(data[0], data[1]))
    