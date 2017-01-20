### MPD Reading and Writing file directory
MPD_READ_DIR                = "/tmp/dash/output"
MPD_WRITE_DIR               = "/tmp/dash/media"
MPD_GET_DIR                 = "dash/media"   #no need to add '/' ahead
MPD_WATCH_PATH              = MPD_READ_DIR

### M3U8 Reading and Writing directory
M3U8_READ_DIR               = "/tmp/hls/output"
M3U8_WRITE_DIR              = "/tmp/hls/media"
M3U8_GET_DIR                = "hls/media/"
M3U8_WATCH_PATH             = M3U8_READ_DIR
GET_BOX_AMOUNT              = 10

### ZMQ SETTINGS
# PUB-SUB MainTaining boxes' connections
ZMQ_MT_TOPIC                = u"MAINTAIN"
ZMQ_MT_SUB_TCP              = "tcp://192.168.1.2:5563"  # Where Sub server connects
ZMQ_MT_PUB_TCP              = ZMQ_MT_SUB_TCP            # Where publish box connects
ZMQ_MT_BOX_UPDATE_SEC       = 3
ZMQ_MT_SERVER_EXPIRE_SEC    = 4
ZMQ_SOCKET_BIND_TIME        = 1
ZMQ_XSUB_ADDRESS            = "tcp://192.168.1.2:6001"  # Where workers connect
ZMQ_XPUB_ADDRESS            = "tcp://192.168.1.2:6000"  # Where media_boxes connect

MEDIA_EXPIRED_TIME          = 60