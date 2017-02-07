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

def logmsg(msg):
    logging.basicConfig(format='%(name)s %(asctime)s:\n %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S')
    logging.warning(msg)

def logwarning(msg):
    logging.basicConfig(format='%(name)s %(asctime)s:\n %(message)s',
                        datefmt='%Y/%m/%d %H:%M:%S')
    logging.error(msg)
    


@app.task
def mother_m3u8_modify(pathname):
    SERVER_IP           = configfile.SERVER_IP
    SERVER_PORT         = configfile.SERVER_PORT
    M3U8_WRITE_FOLDER   = configfile.M3U8_WRITE_DIR.rsplit('/', 1)[1]
    server_http_url     = "http://" + SERVER_IP + ":" + SERVER_PORT + "/" + \
                          M3U8_WRITE_FOLDER + "/"
    try:
        fp = open(pathname, "r+")
    except IOError:
        logwarning(' IOError in mother_m3u8_modify Pathname: %s.'%(pathname))
        return
    fp.seek(0)
    st = []
    line = fp.readline()
    # Read each line in file, modify lines and append it to list
    while line:
        if ".m3u8" in line:
            line = server_http_url + line
        st.append(line)
        line = fp.readline()
    # Write items in list from the beginning of the file
    fp.seek(0)
    for i in st:
        fp.write(i)
    fp.truncate()
    fp.flush()
    fp.close()
    logmsg("Update Mother M3U8 %s."%(pathname))


def box_generator(rdb, m3u8_media_amount):
    box_list = rdb.zrangebyscore(configfile.REDIS_BOX_MEDIA_AMOUNT, 0, 'inf',
                                 start=0, num=m3u8_media_amount)
    logmsg("AVAILABLE BOX NUMBER %d"%(len(box_list)))
    if not box_list:
        yield None
        logwarning("box_generator: No box available.")
    else:
        i = 0
        while True:
            yield box_list[i]
            i = (i+1) % len(box_list)

def assign_media_to_box(rdb, box_generator, expire_media_time,  media_path):
    if not os.path.isfile(media_path) or rdb.exists(media_path):
        return
    box_id = box_generator.next()
    if not box_id:
        logwarning("No available box for %s"%(media_path))
        return
    ip_s, port_s = rdb.hmget(box_id, "IP", "PORT")
    rdb.hmset(media_path, {"BOX_ID":box_id, "IP":ip_s, "PORT":port_s,
                           "CHECK":"False", "ASSIGN_SERVER":"False"})
    rdb.expire(media_path, expire_media_time)
    logmsg("Assign %s IP: %s PORT %s==> %s"%(box_id, ip_s, port_s, media_path))
    
@app.task
def m3u8_trans(pathname):
    """
    - Read line from m3u8
    - Assign each media segment to different boxes
    """
    # Import from configfile
    M3U8_WRITE_DIR      = configfile.M3U8_WRITE_DIR
    M3U8_GET_DIR        = configfile.M3U8_GET_DIR
    m3u8_media_amount   = configfile.M3U8_MEDIA_AMOUNT
    SERVER_IP           = configfile.SERVER_IP
    SERVER_PORT         = configfile.SERVER_PORT
    expire_media_time   = configfile.EXPIRE_MEDIA_TIME
    m3u8_time_waiting   = configfile.M3U8_TIME_WAITING   
    # Connect to redis 
    rdb = redis.StrictRedis(host=configfile.REDIS_HOST)
    # dir_name / stream_name / basename = XXX.mpd,
    path, basename = pathname.rsplit('/', 1)
    dir_name, stream_name = path.rsplit('/', 1)
    # Open read file
    try:
        infile = open(pathname, "r")
    except IOError:
        logwarning('IOError in m3u8_trans() Pathname: %s.'%(pathname))
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
    generator = box_generator(rdb, m3u8_media_amount)
    first_media = True
    line = infile.readline()  
    while line:
        if '.ts' == line.rstrip()[-3:]:
            # Send consecutive media to box in advance
            if first_media:
                head_time = int(line.split('.')[0])
                for timeline in range(head_time, head_time+m3u8_media_amount):
                    time_path = path + '/' + str(timeline) + '.ts'
                    try:
                        assign_media_to_box(rdb, generator, expire_media_time, time_path)
                    except StopIteration:
                        break
                time.sleep(m3u8_time_waiting)
                first_media = False
            ip_s, port_s = [None for i in range(2)]
            media_path = path + '/' + line.rstrip()
            if rdb.hmget(media_path, "CHECK")[0] == "True":
                ip_s, port_s = rdb.hmget(media_path, "IP", "PORT")
            else:
                rdb.hmset(media_path, {"IP":SERVER_IP, "PORT":SERVER_PORT,
                                       "ASSIGN_SERVER":"True"})
                rdb.expire(media_path, expire_media_time)
                ip_s, port_s = [SERVER_IP, SERVER_PORT]
                logmsg("Assign Server IP PORT to media_path: %s"%(media_path))
            # Modify current line
            get_url_prefix = "http://"+ip_s+":"+port_s+"/"
            line = get_url_prefix + M3U8_GET_DIR + stream_name + "/" + line
            # end if
        outfile.write(line)
        line = infile.readline()
    infile.close()
    outfile.truncate()
    outfile.close()

@app.task
def update_M3U8(ip_s, port_s, stream_name, time_segment, m3u8_path):
    """
    time_segment format: <time>.ts
    """
    logmsg("UPDATE M3U8:%s. IP:%s PORT:%s. TIME SEGMENT:%s"%(m3u8_path, ip_s, port_s, time_segment))
    M3U8_GET_DIR = configfile.M3U8_GET_DIR
    get_url_prefix = "http://"+ip_s+":"+port_s+"/"
    try:
        fp = open(m3u8_path, "r+")
    except IOError:
        logwarning(' IOError in update_M3U8() Pathname: %s.'%(m3u8_path))
        return
    fp.seek(0)
    st = []
    line = fp.readline()
    while line:
        if str(time_segment) in line:
            line = get_url_prefix + M3U8_GET_DIR + stream_name +\
                   "/" + time_segment + '\n'
        st.append(line)
        line = fp.readline()
    fp.seek(0)
    for i in st:
        fp.write(i)
    fp.truncate()
    fp.flush()
    fp.close()
    logmsg("Update %s."%(m3u8_path))
    
        
@app.task
def send_media_to_box(media_path):
    """
    Send media tasks to boxes via proxy server
    """
    if not os.path.isfile(media_path):
        logwarning("send_media_to_box: %s file not found"%(media_path))
        return
    context = zmq.Context()
    socket  = context.socket(zmq.PUB)
    socket.connect(configfile.ZMQ_XSUB_ADDRESS)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    rdb = redis.StrictRedis(host=configfile.REDIS_HOST)
    box_id = rdb.hmget(media_path, "BOX_ID")[0]
    media_path = str(media_path)
    try:
        infile = open(media_path, "rb")
    except:
        logwarning("send_media_to_box can't open %s" % (media_path))
        return
    # Use BOX_ID as TOPIC
    data = [box_id, media_path]
    data.append(infile.read())
    rdb.hmset(media_path, {"SEND_TIME":str(time.time())})
    # Send data
    socket.send_multipart(data)
    infile.close()
    socket.close()
    context.term()
    logmsg("Send %s to %s"%(media_path, box_id))
    
@app.task
def send_media_box_update():
    context = zmq.Context()
    socket  = context.socket(zmq.PUB)
    socket.connect(configfile.ZMQ_XSUB_ADDRESS)
    rdb = redis.StrictRedis(host=configfile.REDIS_HOST)
    time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
    for box_id in rdb.keys("box-*"):
        data = [box_id, "Update"]
        socket.send_multipart(data)
    socket.close()
    