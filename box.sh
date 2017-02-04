#! /bin/sh
### BEGIN INIT INFO
# Provides:          live_platform
# Required-Start:
# Required-Stop:     
# Should-Stop:       
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start box default process
# Description:       Start redis and nginx server, and start 
#                    box default process of live_platform
#                    
### END INIT INFO

# RAMDISK SETTINGS
RAMDISK_SIZE=200
RAMDISK_PATH=/tmp/hls
# Nginx SETTINGS
NGINX_PATH=/usr/local/nginx/sbin/nginx
NGINX_HTTP_PORT=8000
# PACKAGE SETTINGS
PACKAGE_PATH=/root/live_platform
BOX_FILE=run_box.py
PROCESS_NUMBER=4	#Number of Multiprocess for box
# BASH SETTINGS
PROCESS_NAME=run_box

start() {
	# Create ramdisk
	mkdir -p $RAMDISK_PATH
	mount -t tmpfs -o size=${RAMDISK_SIZE}M tmpfs ${RAMDISK_PATH}
	# Start Nginx server
	/usr/local/nginx/sbin/nginx
	# Start Redis server
	redis-server --daemonize yes
	# Start box process by create a new screen
	if [ -e $PACKAGE_PATH ];then
		screen -dm python $PACKAGE_PATH/$BOX_FILE ${NGINX_HTTP_PORT} ${PROCESS_NUMBER}
	else
		echo -e "PACKAGE MISSING, CAN'T START PROCESS"	
	fi
}

stop() {
	/usr/local/nginx/sbin/nginx -s stop
	redis-cli shutdown
	pkill -9 python
}

### main logic ###
case "$1" in
	start)
		start
        ;;
    stop)
        stop
        ;;
    status)
        ;;
    restart|reload|condrestart)
        stop
        start
        ;;
    *)
        echo $"Usage: $0 {start|stop|restart|reload|status}"
        exit 1
esac
  
exit 0

