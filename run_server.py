from server.zmq_server import run_zmq_SUB_server, expire_box_set_members
import multiprocessing
import zmq
import time
import configfile
import redis

if __name__ == '__main__':
    try:
        rdb = redis.StrictRedis(host=configfile.REDIS_HOST)
        server_process      = multiprocessing.Process(target=run_zmq_SUB_server, args=(rdb,))
        expire_box_process  = multiprocessing.Process(target=expire_box_set_members, args=(rdb,))
        server_process.start()
        expire_box_process.start()
        context         = zmq.Context()
        socket_sub      = context.socket(zmq.SUB)
        socket_pub      = context.socket(zmq.PUB)
        socket_sub.bind(configfile.ZMQ_XSUB_ADDRESS)
        socket_sub.setsockopt(zmq.SUBSCRIBE, '')
        socket_pub.bind(configfile.ZMQ_XPUB_ADDRESS)
        time.sleep(configfile.ZMQ_SOCKET_BIND_TIME)
        zmq.proxy(socket_pub, socket_sub)
    except KeyboardInterrupt:
        expire_box_process.terminate()
        server_process.terminate()
        server_process.join()