import pyinotify
import configfile
from server.tasks import mpd_trans, m3u8_trans, logmsg

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MOVED_TO(self, event):
        if "m3u8" == event.pathname[-4:]:
            m3u8_trans.delay(event.pathname)
            logmsg("EventHandler process_IN_MOVED_TO: %s"%(event.pathname))
            
            
if __name__ == '__main__':
    wm         = pyinotify.WatchManager() # Watch Manager
    mask       = pyinotify.IN_MOVED_TO
    handler    = EventHandler()
    notifier   = pyinotify.Notifier(wm, handler)
    #wm.add_watch(configfile.MPD_WATCH_PATH, mask, rec=True, auto_add=True)
    wm.add_watch(configfile.M3U8_WATCH_PATH, mask, rec=True, auto_add=True)
    print("Notifier start loop...")
    notifier.loop()
