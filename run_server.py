from server.zmq_server import zmq_SUB_server


if __name__ == '__main__':
    server = zmq_SUB_server()
    server.run()