import sys
import configfile
import uuid
import time
import multiprocessing
import redis
from box.zmq_box import run_zmq_PUB_BOX, run_zmq_MEDIA_BOX, recycle_expired_boxes


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print ("python run_box.py [ip] [port] [box_amount]")
        sys.exit(1)
    IP          = sys.argv[1]
    PORT        = sys.argv[2]
    BOX_AMOUNT  = sys.argv[2]
    box_process = []
    rdb         = redis.StrictRedis(host=configfile.REDIS_HOST)
    try:
        for i in range(BOX_AMOUNT):
            # GET RAMDOM UUID to set as box id
            box_id = "box-"+str(uuid.uuid4())
            print("Your Box %d ID: %s "%(i+1, str(box_id)))
            # Create MEDIA_BOX and PUB_BOX thread and run it
            get_media_process = multiprocessing.Process(name="Media_Box %d"%(i+1),
                                                        target=run_zmq_MEDIA_BOX,
                                                        args=(box_id, IP, PORT, rdb))
            publish_process = multiprocessing.Process(name="Publish_Box %d"%(i+1),
                                                      target=run_zmq_PUB_BOX,
                                                      args=(box_id, IP, PORT, rdb))
            
            get_media_process.start()
            publish_process.start()
            box_process.append((get_media_process, publish_process))
        recycle_process = multiprocessing.Process(name="Recycle Process",
                                                  target=recycle_expired_boxes,
                                                  args=(rdb,))
        recycle_process.start()
        while True:
            for i in range(BOX_AMOUNT):
                if not box_process[i][0].is_alive():
                    box_process[i][0].start()
            time.sleep(3)
    except KeyboardInterrupt:
        for i in range(BOX_AMOUNT):
            box_process[i][0].terminate()
            box_process[i][1].terminate()
            box_process[i][0].join()
            box_process[i][1].join()
        recycle_process.terminate()
        recycle_process.join()
        print("stop")