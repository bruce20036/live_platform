import sys
import configfile
from src.box.zmq_box import zmq_PUB_BOX


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print ("python run_zmq_PUB_BOX [box_id]")
        sys.exit(1)
    #Create box instance
    publish_box = zmq_PUB_BOX(sys.argv[1], configfile.ZMQ_MT_TCP)
    #Start
    publish_box.run(configfile.ZMQ_MT_TOPIC)
    