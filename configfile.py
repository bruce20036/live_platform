"""
NOTE!!!
1. box id should be "box-(UUID)"
2. 

"""

#Notify watching directory
NOTIFY_WATCH_PATH = "/tmp/dash"

#MPD Reading and Writing file directory
MPD_READ_DIR = "/tmp/dash/output/test"
MPD_WRITE_DIR = "/tmp/dash/mpd"
MPD_GET_DIR = "dash/output/media"   #no need to add '/' ahead
#MEDIA_OUTPUT_FOLDER / STREAM_NAME / MEDIA_NAME(m4a,m4v)
MEDIA_OUTPUT_FOLDER = "/tmp/dash/mpd"

### QUEUE_NAME
#Used for transfering m4v and m4a 
MEDIA_QUEUE = "MEDIA_QUEUE"

###ZMQ SETTINGS
#PUB-SUB MainTaining boxes' connections
ZMQ_MT_TOPIC = u"MAINTAIN"
ZMQ_MT_PUB_TCP = "tcp://127.0.0.1:5563"
ZMQ_MT_SUB_TCP = "tcp://127.0.0.1:5563"
ZMQ_MT_BOX_UPDATE_SEC = 3

#PUB-SUB FOR m4a and m4v TO DISTRIBUTE ACROSS BOXES
ZMQ_MEDIA_DISTRIBUTE_PUB_TCP = "tcp://127.0.0.1:5558"
ZMQ_MEDIA_DISTRIBUTE_SUB_TCP = "tcp://127.0.0.1:5558"



