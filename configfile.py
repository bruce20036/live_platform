### MPD Reading and Writing file directory
MPD_READ_DIR                = "/tmp/dash/output"
MPD_WRITE_DIR               = "/tmp/dash/media"
MPD_GET_DIR                 = "dash/media"   #no need to add '/' ahead
MPD_WATCH_PATH              = MPD_READ_DIR

### M3U8 Reading and Writing directory
M3U8_READ_DIR               = "/tmp/hls/output"
M3U8_WRITE_DIR              = "/tmp/hls/media"
M3U8_GET_DIR                = "hls/media/"
MEDIA_GET_DIR               = "hls/output/"
BOX_MEDIA_WRITE_DIR         = "/tmp/hls/output"
M3U8_WATCH_PATH             = M3U8_READ_DIR
M3U8_MEDIA_AMOUNT           = 12
M3U8_TIME_WAITING           = 1.0   #seconds (use float)

### ZMQ SETTINGS
# PUB-SUB MainTaining boxes' connections
ZMQ_MT_TOPIC                = u"MAINTAIN"
ZMQ_VERIFY_TOPIC            = u"RECEIVED"
ZMQ_MT_SUB_TCP              = "tcp://140.115.153.211:5563"  # Where Sub server connects
ZMQ_MT_PUB_TCP              = ZMQ_MT_SUB_TCP            # Where publish box connects
ZMQ_MT_BOX_UPDATE_SEC       = 3
ZMQ_MT_SERVER_EXPIRE_SEC    = 4
ZMQ_SOCKET_BIND_TIME        = 1
ZMQ_XSUB_ADDRESS            = "tcp://140.115.153.211:6001"  # Where workers connect
ZMQ_XPUB_ADDRESS            = "tcp://140.115.153.211:6000"  # Where media_boxes connect

# SERVER's HTTP Server IP PORT
SERVER_IP                   = "140.115.153.211"
SERVER_PORT                 = "8000"
MEDIA_BOX_UDPATE_DURATION   = 9   # Server will send it every    MEDIA_BOX_UDPATE_DURATION/3
SEND_MEDIA_QUEUE_NAME       = "SEND_MEDIA_QUEUE"

# Redis settings
REDIS_HOST                  = '127.0.0.1'
REDIS_BOX_SET               = "box_set"     # key
REDIS_BOX_MEDIA_AMOUNT      = "redis_box_media_amount"  #key
EXPIRE_BOX_TIME             = 10
BOX_EXPIRE_MEDIA_TIME       = 60  # In box's redis
EXPIRE_MEDIA_TIME           = 60  # To expire media_path hash in server's redis
