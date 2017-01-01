import signal
from src.server.threadnotify import ThreadedNotifyDistributor
from tasks import fetch_url


#Stop thread if CTRL+C occurs
def catch(signum, frame):
    global thread
    thread.stop()


if __name__ == '__main__':
    #Create Thread and start it!
    thread = ThreadedNotifyDistributor()
    thread.start()
