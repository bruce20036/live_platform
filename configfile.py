#Notify watching directory
NOTIFY_WATCH_PATH = "/tmp/dash"

#MPD Reading and Writing file directory
MPD_READ_DIR = "/tmp/dash/output/test"
MPD_WRITE_DIR = "/tmp/dash/mpd"
MPD_GET_DIR = "dash/output/"   #no need to add '/' ahead


###ZMQ SETTINGS
#PUB-SUB MainTaining boxes' connections
ZMQ_MT_TOPIC = "MAINTAIN"
ZMQ_MT_TCP = "tcp://*:5563"
ZMQ_MT_BOX_UPDATE_SEC = 3

