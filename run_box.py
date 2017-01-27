import sys
import configfile
import uuid
import time
from multiprocessing import Process
import redis
import requests
from box.zmq_box import Box, recycle_expired_boxes

GET_IP_URL = 'https://api.ipify.org?format=json'

def get_ip():
    #return str(requests.get(GET_IP_URL).json()["ip"])
    return "0.0.0.0"
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ("python run_box.py [port] [box_amount]")
        sys.exit(1)
    IP          = get_ip()
    PORT        = sys.argv[1]
    BOX_AMOUNT  = int(sys.argv[2])
    box_list    = []
    rdb         = redis.StrictRedis(host=configfile.REDIS_HOST)
    for item in rdb.keys("Expired*"):
        rdb.delete(item)
    try:
        for i in range(BOX_AMOUNT):
            # GET RAMDOM UUID to set as box id
            box_id = "box-"+str(uuid.uuid4())
            print("Your Box %d ID: %s "%(i+1, str(box_id)))
            box = Box(box_id, i+1, IP, PORT)
            box.start(rdb)
            box_list.append(box)
        recycle_process = Process(name="Recycle Process",
                                  target=recycle_expired_boxes,
                                  args=(rdb,))
        recycle_process.start()
        while True:
            for i in range(BOX_AMOUNT):
                if not box_list[i].media_process_is_alive():
                    box_list[i].stop_media_process()
                    box_list[i].start_media_process(rdb)
            check_ip = get_ip()
            if IP != check_ip:
                IP = check_ip
                for i in range(BOX_AMOUNT):
                    box_list[i].stop_publish_process()
                    box_list[i].update_IP(IP)
                    box_list[i].start_publish_process(rdb)
            time.sleep(2)
    except KeyboardInterrupt:
        for i in range(BOX_AMOUNT):
            box_list[i].stop()
        recycle_process.terminate()
        recycle_process.join()
        print("Stop")   