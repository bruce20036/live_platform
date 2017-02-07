import pyinotify
import configfile
import redis
from server.tasks import logmsg, m3u8_trans, mother_m3u8_modify, send_media_to_box

class EventHandler(pyinotify.ProcessEvent):
    def my_init(self, rdb):
        self.rdb = rdb
        
    def process_IN_MOVED_TO(self, event):
        if "m3u8" != event.pathname[-4:]: return
        pre, post = event.pathname.rsplit('/', 1)
        if pre == configfile.M3U8_READ_DIR:
            mother_m3u8_modify.delay(event.pathname)
        else:
            m3u8_trans.delay(event.pathname)
        logmsg("EventHandler process_IN_MOVED_TO: %s"%(event.pathname))
    
    def process_IN_CLOSE_WRITE(self, event):
        if ".ts" == event.pathname[-3:]:
            self.rdb.hmset(event.pathname, {"TS_COMPLETE":True})
            send_media_to_box.delay(event.pathname)
            logmsg("EventHandler process_IN_CLOSE_WRITE: %s"%(event.pathname))
            
            
if __name__ == '__main__':
    rdb        = redis.StrictRedis(host=configfile.REDIS_HOST)
    wm         = pyinotify.WatchManager() # Watch Manager
    mask       = pyinotify.IN_MOVED_TO | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE
    handler    = EventHandler(rdb=rdb)
    notifier   = pyinotify.Notifier(wm, handler)
    wm.add_watch(configfile.M3U8_WATCH_PATH, mask, rec=True, auto_add=True)
    print("Notifier start loop...")
    notifier.loop()
