import os
import random
import time
import subprocess
import logging
import zmq
import redis
import configfile
from start_celery import app
try:
    import Queue as queue # version < 3.0
except ImportError:
    import queue

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
    
            if part == 1 and not rdb.sismember(path, time_name):
                print path, " ", time_name
                m4v_path = path+"/"+time_name+".m4v"
                m4a_path = path+"/"+time_name+".m4a"
                send_media_to_box.delay(box, m4v_path)
                send_media_to_box.delay(box, m4a_path)
                rdb.sadd(path, time_name)
            
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
            send_media_to_box.delay(box, media_path)
            
        elif "audio/mp4" in line:
            part = 2
            outfile.write(line)
            
        else:
            outfile.write(line)
        line = infile.readline()
        # End while
    # Close file
    rdb.expire(path, 200)
    outfile.truncate()
    infile.close()
    outfile.close()



def box_generator(rdb, stream_path, box_amount=10):
    """
    - Use Redis sorted set to achieve load balance among box
    - Get next available box by next() 
    """
    random.seed(int(time.time()))
    # GET a list of box, try 5 times , if there's no avaiable
    # box then log error and return
    for test in range(5):
        box_list = rdb.keys("box*")
        if len(box_list) > 0:
            break
        time.sleep(1)    
    if len(box_list) == 0:
        raise Exception("box_generator: No Box Exists in Redis")
    stream_set = rdb.zrange(stream_path, 0, -1)
    while len(box_list) > 0 and box_amount > 0:
        box = random.choice(box_list)
        if not stream_set or not box in stream_set:
            rdb.zadd(stream_path, 0, box)
        box_list.remove(box)
        box_amount-=1
    while True:
        box = rdb.zrangebyscore(stream_path, 0, '+inf', start=0, num=1)[0]
        if not rdb.exists(box):
            rdb.zrem(stream_path, box)  # Remove box if not exists anymore
            continue
        ip, port = rdb.hmget(box, "IP", "PORT")
        rdb.zincrby(stream_path, box)    # Increment box's score by 1
        yield box, ip, port
    
@app.task
def m3u8_trans(pathname):
    # Import from configfile
    M3U8_WRITE_DIR  = configfile.M3U8_WRITE_DIR
    M3U8_GET_DIR    = configfile.M3U8_GET_DIR
    GET_BOX_AMOUNT  = configfile.GET_BOX_AMOUNT
    # Connect to redis 
    rdb = redis.StrictRedis()
    # dir_name / stream_name / basename = XXX.mpd,
    path, basename = pathname.rsplit('/', 1)
    dir_name, stream_name = path.rsplit('/', 1)
    # Open read file
    try:
        infile = open(pathname, "r")
    except IOError:
        logmsg(' IOError in m3u8_trans() Pathname: %s.'%(pathname))
        return
    # m3u8 output path
    output_folder = os.path.join(M3U8_WRITE_DIR, stream_name)
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
    try:
        generator = box_generator(rdb, path, GET_BOX_AMOUNT)
    except Exception as e:
        logmsg(str(e))
        return
    line = infile.readline()
    while line:
        if '.ts' == line.rstrip()[-3:]:
            media_path = path + '/' + line.rstrip()
            box_id = rdb.get(media_path)
            if not box_id:
                box_id, ip_s, port_s = generator.next()
                send_media_to_box.delay(box_id, media_path)
            else:
                ip_s, port_s = rdb.hmget(box_id, "IP", "PORT")
            get_url_prefix = "http://"+ip_s+":"+port_s+"/"
            line = get_url_prefix + M3U8_GET_DIR + stream_name + "/" + line
            rdb.set(media_path, box_id)
        outfile.write(line)
        line = infile.readline()
    infile.close()
    outfile.truncate()
    outfile.close()
    rdb.expire(path, 30)
    
      
@app.task
def send_media_to_box(box_id, media_path):
    """
    Send media tasks to boxes via proxy server
    """
    global context
    socket = context.socket(zmq.PUB)
    socket.connect(configfile.ZMQ_XSUB_ADDRESS)
    time.sleep(0.05)
    box_id = str(box_id)
    media_path = str(media_path)
    print media_path
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
    
