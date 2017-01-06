import os
import random
import time
import subprocess
import logging
import zmq
import redis
import configfile
from start_celery import app

# Create global context
context = zmq.Context()


def logmsg(msg):
    logging.basicConfig(format='%(asctime)s Message: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.warning(msg)
    

@app.task
def mpd_trans(pathname):
    """
    Get a list of boxes from redis, then insert box's IP PORT to MPD file.
    At the same time, push it to queue for worker to execute send_media_to_box
    """
    # Connect to redis in order to get box's queryset
    rdb = redis.StrictRedis()
    random.seed(int(time.time()))
    
    # GET a list of box, try 5 times , if there's no avaiable
    # box then log error and return
    test = 5
    while test > 0:
        box_list = rdb.keys("box*")
        if len(box_list) > 0:
            break
        time.sleep(1)
        test -= 1
        
    if len(box_list) == 0:
        logmsg("mpd_trans: No box in list")
        return
    
    box = random.choice(box_list)
    
    ip_s, port_s = rdb.hmget(box, "IP", "PORT")
    ip = "http://"+ip_s+":"+port_s+"/"
    ip_mpd = "http://"+ip_s+":"+"8000"+"/"
    
    # dir_name / stream_name / basename = XXX.mpd,
    path, basename = pathname.rsplit('/', 1)
    dir_name, stream_name = path.rsplit('/', 1)
    
    # Open read file
    try:
        infile = open(pathname, "r")
    except IOError:
        logmsg(' IOError in mpd_trans() Pathname: %s.'%(pathname))
        return
    
    # Mpd output path
    output_folder = os.path.join(configfile.MPD_WRITE_DIR, stream_name)
    output_dir = os.path.join(output_folder, basename)
    # Check if the dir is created
    if not os.path.isdir(output_folder):
        subprocess.check_output(['mkdir', '-p', output_folder])
 
    # Open output file
    if not os.path.exists(output_dir):
        outfile = open(output_dir, "w")
        outfile.close()
    outfile = open(output_dir, "r+")
    outfile.seek(0)
    
    line = infile.readline()
    part = 1
    
    while line:
        if "<S t=" in line:
            pre_str, time_name, post_str = line.split("\"", 2)
            outfile.write(line)
            if part == 1:
                media_path = path+"/"+time_name+".m4v"
            else:
                media_path = path+"/"+time_name+".m4a"
            
            send_media_to_box.delay(box, ip_s, port_s, media_path)
                
        elif "media" in line:
            pre_str, post_str = line.split("\"", 1)
            concentrate_str = (pre_str + "\"" + ip_mpd +
                               configfile.MPD_GET_DIR + "/" +
                               stream_name + "/" + post_str)
            outfile.write(concentrate_str+'\n')
            
        elif "initialization" in line:
            pre_str, post_str = line.split("\"", 1)
            #  media="ip/dash/output/stream_name/init.m4a"
            concentrate_str = (pre_str + "\"" + ip_mpd +
                               configfile.MPD_GET_DIR + "/" +stream_name +
                               "/" + post_str)
            outfile.write(concentrate_str+'\n')

            if part == 1:
                media_path = path + "/init.m4v"
            else:
                media_path = path + "/init.m4a"
            send_media_to_box.delay(box, ip_s, port_s, media_path)
            
        elif "audio/mp4" in line:
            part = 2
            outfile.write(line)
            
        else:
            outfile.write(line)
        line = infile.readline()
        # End while
    # Close file
    outfile.truncate()
    infile.close()
    outfile.close()


@app.task
def send_media_to_box(box_id, box_ip, box_port, media_path):
    """
    Send m4a and m4v tasks to boxes via proxy server
    """
    global context
    socket = context.socket(zmq.PUB)
    socket.connect(configfile.ZMQ_XSUB_ADDRESS)
    time.sleep(0.0001)
    box_id = str(box_id)
    media_path = str(media_path)
    try:
        infile = open(media_path, "rb")
    except:
        logmsg("send_media_to_box can't open %s" % (media_path))
        return
    
    # Use BOX_ID as TOPIC
    data = [box_id, media_path]
    data.append(infile.read())
    # Send data
    socket.send_multipart(data)
    infile.close()
    socket.close()
    
