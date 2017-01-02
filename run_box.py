import sys
import signal
import configfile
import uuid
import time
import multiprocessing
from box.zmq_box import run_zmq_PUB_BOX, run_zmq_MEDIA_BOX


def stop_process(signum, frame):
    global publish_process
    global get_media_process
    # Stop process and wait it to join in
    publish_process.terminate()
    get_media_process.terminate()
    publish_process.join()
    get_media_process.join()
    print("stop")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ("python run_box.py [ip] [port]")
        sys.exit(1)
    IP = sys.argv[1]
    PORT = sys.argv[2]
    
    # GET RAMDOM UUID to set as box id
    box_id = "box-"+str(uuid.uuid4())
    print("Your Box ID: "+box_id)
    # Create MEDIA_BOX and PUB_BOX thread and run it
    publish_process = multiprocessing.Process(name="Publish_Box",
                                              target=run_zmq_PUB_BOX,
                                              args=(box_id, IP, PORT,))
    get_media_process = multiprocessing.Process(name="Media_Box",
                                                target=run_zmq_MEDIA_BOX,
                                                args=(box_id, IP, PORT,))
    publish_process.start()
    get_media_process.start()
    # Set signal to stop processes when CTRL+C occurs
    signal.signal(signal.SIGINT, stop_process)
 
    
    
    

    