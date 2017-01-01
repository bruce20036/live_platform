import pyinotify
import configfile
from server.tasks import mpd_trans

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MOVED_TO(self, event):
        #if not mpd file or the current mpd has been dealt with other thread,
        #then ignore it
        if "mpd" == event.pathname[-3:]:
            mpd_trans.delay(event.pathname)
            print("EventHandler process_IN_MOVED_TO: %s"%(event.pathname))
            


if __name__ == '__main__':
    watch_path = configfile.NOTIFY_WATCH_PATH
    wm         = pyinotify.WatchManager() # Watch Manager
    mask       = pyinotify.IN_MOVED_TO
    handler    = EventHandler()
    notifier   = pyinotify.Notifier(wm, handler)
    wm.add_watch(watch_path, mask, rec=True, auto_add=True)
    print("MPD Notifier start loop...")
    notifier.loop()
    
    
    




