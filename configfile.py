### Notify watching directory
NOTIFY_WATCH_PATH           = "/tmp/dash/output"

### MPD Reading and Writing file directory
MPD_READ_DIR                = "/tmp/dash/output/test"
MPD_WRITE_DIR               = "/tmp/dash/media"
MPD_GET_DIR                 = "dash/output/media"   #no need to add '/' ahead
# MEDIA_OUTPUT_FOLDER / STREAM_NAME / MEDIA_NAME(m4a,m4v)
MEDIA_OUTPUT_FOLDER         = "/tmp/dash/media"


### ZMQ SETTINGS
# PUB-SUB MainTaining boxes' connections
ZMQ_MT_TOPIC                = u"MAINTAIN"
ZMQ_MT_PUB_TCP              = "tcp://127.0.0.1:5563"
ZMQ_MT_SUB_TCP              = "tcp://127.0.0.1:5563"
ZMQ_MT_BOX_UPDATE_SEC       = 3
ZMQ_MT_SERVER_EXPIRE_SEC    = 4



