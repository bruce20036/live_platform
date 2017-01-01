import requests
import random, time, subprocess, logging
import zmq
import configfile
from start_celery import app


@app.task
def mpd_trans(pathname):
    ### Connect to redis in order to get box's queryset
    redis = redis.StrictRedis()
    random.seed(int(time.time()))
    box = random.choice(redis.keys("box*"))
    ip_s, port_s = redis.hmget(box, "IP", "PORT")
    ip = "http://"+ip_s+":"+port_s+"/"
    ip_mpd = "http://"+ip_s+":"+"8000"+"/"
    
    #dir_name / stream_name / basename = XXX.mpd,
    path, basename = pathname.rsplit('/', 1)
    dir_name, stream_name = path.rsplit('/', 1)
    
    #mpd output path
    output_folder = os.path.join(configfile.MPD_WRITE_DIR, stream_name)
    output_dir = os.path.join(output_folder, basename)
    #Check if the dir is created
    if not os.path.isdir(output_folder):
        subprocess.check_output(['mkdir', '-p', output_folder])
    
    #open read file
    try:
        infile = open(pathname,"r")
    except IOError:
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        logging.warning(' IOError in mpd_trans().')
        return
 
    #open output file
    if not os.path.exists(output_dir):
        outfile = open(output_dir, "w")
        outfile.close()
    outfile = open(output_dir, "r+")
    outfile.seek(0)
    
    line = infile.readline()

    while line:
        if "<S t=" in line:
            pre_str, time_name, post_str = line.split("\"", 2)
            outfile.write(line)
            if part==1:
                media_path = path+"/"+time_name+".m4v"
            else:
                media_path = path+"/"+time_name+".m4a"
            
            send_media_to_box.delay(box, media_path)
                
        elif "media" in line:
            pre_str, post_str = line.split("\"", 1)
            concentrate_str = pre_str +"\""+ ip_mpd \
                             + configfile.MPD_GET_DIR + stream_name + "/" + post_str
                            #    dash/output/        stream_name    /
            outfile.write(concentrate_str+'\n')
            
            
        elif "initialization" in line:
    
            pre_str, post_str = line.split("\"", 1)
                            #  media=    "   ip  
            concentrate_str = pre_str +"\""+ ip_mpd \
                             + configfile.MPD_GET_DIR + stream_name + "/" + post_str
                            #    /dash/output/        stream_name    /     init.m4a"
            outfile.write(concentrate_str+'\n')

            if part==1:
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
        #end while
        
    #close file
    outfile.truncate()
    infile.close()
    outfile.close()


@app.task
def send_media_to_box(box_id, media_path):    
    ### Create zmq instance and bind to tcp
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(configfile.ZMQ_MEDIA_DISTRIBUTE_TCP)
    
    ### OPEN MEDIA FILE in read binary mode
    infile = open(media_path,"rb")
    
    ### Use BOX_ID as TOPIC
    data = [box_id, media_path, ]
    data.append(infile.read()) 
    
    ### Send data
    socket.send_multipart(data)
    
    socket.close()
    context.term()


    