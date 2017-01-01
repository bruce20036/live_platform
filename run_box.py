import sys, signal
import configfile
import uuid
from box.zmq_box import zmq_MEDIA_BOX, zmq_PUB_BOX


def stop_thread(signum, frame):
    global media_box
    global publish_box
    
    ###Stop thread and wait it to join in
    media_box.stop()
    publish_box.stop()
    
    media_box.join()
    publish_box.join()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ("python run_box.py [ip] [port]")
        sys.exit(1)
    IP = sys.argv[1]
    PORT = sys.argv[2]
    
    #GET RAMDOM UUID to set as box id
    box_id = "box-"+str(uuid.uuid4())
    print("Your Box ID: "+box_id)
    
    #Create MEDIA_BOX and PUB_BOX thread and run it
    publish_box = zmq_PUB_BOX(box_id, IP, PORT)
    publish_box.run(configfile.ZMQ_MT_TOPIC)
    media_box = zmq_MEDIA_BOX(box_id)
    media_box.run()
    
    
    #set signal to stop when CTRL+C occurs
    signal.signal(signal.SIGINT, stop_thread)
    
    
    

    