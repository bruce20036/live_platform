from server.zmq_server import zmq_SUB_server, zmq_PROXY_server
import multiprocessing

if __name__ == '__main__':
    try:
        proxy_process   = multiprocessing.Process(target=zmq_PROXY_server)
        proxy_process.start()
        server          = zmq_SUB_server()
        server.run()
    except KeyboardInterrupt:
        proxy_process.terminate()
        proxy_process.join()
