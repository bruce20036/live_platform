import signal
from src.server.threadnotify import ThreadedNotifyDistributor
from tasks import fetch_url



def catch(signum, frame):
    global thread
    thread.stop()


if __name__ == '__main__':
    func(["http://google.com", "https://amazon.in", "https://facebook.com", "https://twitter.com", "https://alexa.com"])
    thread = ThreadedNotifyDistributor()
    thread.start()
    signal.signal(signal.SIGINT, catch)