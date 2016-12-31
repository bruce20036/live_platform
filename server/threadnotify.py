import pyinotify
from tasks import mpd_trans
  
class ThreadedNotifyDistributor(object):
    def __init__(self, watchpath):
        self.watchpath = watchpath
        self.wm       = pyinotify.WatchManager() # Watch Manager
        self.mask     = pyinotify.IN_MOVED_TO
        self.handler = EventHandler()
        self.notifier = pyinotify.ThreadedNotifier(self.wm, self.handler)
        
    def start(self):
        #Set watch path
        self.wm.add_watch(self.watchpath, self.mask, rec=True, auto_add=True)
        # Daemonize to ensure thread dies on exit
        self.notifier.daemon = True
        # Run start() method inherited from threading.Thread
        self.notifier.start()
        print("START ThreadedNotifyDistributor...")
    
    def stop(self):
        self.notifier.stop()

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MOVED_TO(self, event):
        #if not mpd file or the current mpd has been dealt with other thread,
        #then ignore it
        if "mpd" == event.pathname[-3:]:
            mpd_trans.delay(pathname)