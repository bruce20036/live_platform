from celery import Celery
from .. import settings
import requests

#Create Celery app from celeryconfig
app = Celery()
app.config_from_object('celeryconfig')


@app.task
def mpd_trans(pathname):
    path, basename = pathname.rsplit('/', 1)
    dir_name, stream_name = path.rsplit('/', 1)
    output_folder = os.path.join(settings.MPD_WRITE_DIR, stream_name)
    output_dir = os.path.join(output_folder, basename)
    
    #Check if the dir is created
    if not os.path.isdir(output_folder):
        subprocess.check_output(['mkdir', '-p', output_folder])
    #global variable to store boxes and its socket
    #list [ipport, fp, box_id]
    total_box = len(box_set)
    box_counter = 0   
    part = 1
        
    #open file
    try:
        infile = open(pathname,"r")
    except IOError:
        return
 
    if not os.path.exists(output_dir):
        f = open(output_dir, "w")
        f.close()
        
    outfile = open(output_dir, "r+")
    outfile.seek(0)
    fq = open(settings.BASE_DIR+"/gogo.txt", "a")
    fq.write("START mpd\n")
    
    # Read the first line 
    line = infile.readline()
    
    fq.close()
    

    
    ## If the file is not empty keep reading line one at a time
    ## till the file is empty
    while line:
        if "<S t=" in line:
            ip_s, port_s = box_set[box_counter][0]
            ip = "http://"+ip_s+":"+port_s+"/"
            ip_mpd = "http://"+ip_s+":"+"8000"+"/"
            
            pre_str, time_name, post_str = line.split("\"", 2)
            
                           #  <S t  =    "  ip:port       
            
            outfile.write(line)
            if part==1:
                url = ip + settings.MPD_GET_DIR + stream_name+ "/"+time_name+".m4v"
            else:
                url = ip + settings.MPD_GET_DIR + stream_name+ "/"+time_name+".m4a"
            try:
                task.put([box_set[box_counter][2],url])
            except requests.ConnectionError:
                pass
            
            box_counter+=1
            if box_counter == total_box:
                box_counter = 0
                
        elif "media" in line:
            ip_s, port_s = box_set[box_counter][0]
            ip = "http://"+ip_s+":"+port_s+"/"
            ip_mpd = "http://"+ip_s+":"+"8000"+"/"
            pre_str, post_str = line.split("\"", 1)
            concentrate_str = pre_str +"\""+ ip_mpd \
                             + settings.MPD_GET_DIR + stream_name + "/" + post_str
                            #    dash/output/        stream_name    /
            outfile.write(concentrate_str+'\n')
            box_counter+=1
            if box_counter == total_box:
                box_counter = 0
            
        elif "initialization" in line:
            ip_s, port_s = box_set[box_counter][0]
            ip = "http://"+ip_s+":"+port_s+"/"
            ip_mpd = "http://"+ip_s+":"+"8000"+"/"
            
            pre_str, post_str = line.split("\"", 1)
                            #  media=    "   ip  
            concentrate_str = pre_str +"\""+ ip_mpd \
                             + settings.MPD_GET_DIR + stream_name + "/" + post_str
                            #    /dash/output/        stream_name    /     init.m4a"
            outfile.write(concentrate_str+'\n')

            if part==1:
                url = ip + settings.MPD_GET_DIR + stream_name+ "/init.m4v"
            else:
                url = ip + settings.MPD_GET_DIR + stream_name+ "/init.m4a"
            task.put([box_set[box_counter][2],url])
            box_counter+=1
            if box_counter == total_box:
                box_counter = 0
           
        
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
def fetch_url(url):
    resp = requests.get(url)
    print resp.status_code



    