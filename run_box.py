import sys
import configfile
import uuid
import time
from multiprocessing import Process
import redis
import requests
from box.zmq_box import Box, recycle_expired_boxes

GET_IP_URL = 'https://api.ipify.org?format=json'

def stop_all_process(box_list, BOX_AMOUNT):
    for i in range(BOX_AMOUNT):
        box_list[i].stop()
        

def start_all_process(rdb, box_list, BOX_AMOUNT):
    for i in range(BOX_AMOUNT):
        box_list[i].start(rdb)


def get_ip():
    return str(requests.get(GET_IP_URL, timeout=3).json()["ip"])



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ("python run_box.py [port] [box_amount]")
        sys.exit(1)
    try:
        IP = get_ip()
    except  requests.exceptions.RequestException as e:
        IP = None
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
            if IP: box.start(rdb)
            box_list.append(box)
        recycle_process = Process(name="Recycle Process",
                                  target=recycle_expired_boxes,
                                  args=(rdb,))
        recycle_process.start()
        while True:
            check_ip = ''
            try:
                check_ip = get_ip()
            except  requests.exceptions.RequestException as e:
                print e
                stop_all_process(box_list, BOX_AMOUNT)
                continue
            if IP != check_ip:
                print "IP CHANGED: %s -> %s"%(IP, check_ip)
                IP = check_ip
                stop_all_process(box_list, BOX_AMOUNT)
                for i in range(BOX_AMOUNT):
                    box_list[i].update_IP(IP)
            start_all_process(rdb, box_list, BOX_AMOUNT)
    except KeyboardInterrupt:
        for i in range(BOX_AMOUNT):
            box_list[i].stop()
        recycle_process.terminate()
        recycle_process.join()
        print("Stop")   