# live_platform

##Implementation
- Live streaming through RTMP 
- Server generates MPD file and m4v, m4a.
- Workers distribute .m4v & .m4a to boxes via zeromq
- Clients watch live channel and take m4v and m4a files from boxes instead of server

##Start project
###Before Starting
- Change configuration in configfile and celeryconfig
- For Server: 

In configfile, change ZMQ_MT_PUB_TCP and ZMQ_MT_PUB_TCP to your correct IP Address
- For Box side:

In configfile, ZMQ_MT_PUB_TCP and ZMQ_MT_PUB_TCP need be same as server side's ZMQ_MT_PUB_TCP and ZMQ_MT_PUB_TCP
- For celery worker:

In celeryconfig, change broker_url and result_backend to corrent url (In other words, which means substituting your ip address for "localhost")

###Server Side
1. Start Nginx
2. Start Redis
```
redis-server --daemonize yes
```
3. Open two terminal and start mpd_notifier and server respectively

```
python run_server.py
python run_notifier.py
```


###Box Side (Be careful that IP PORT(where zmq bind to) should not be same as nginx web server ip port)
1. Start Redis
2. append http server ip port
```
python run_box.py [IP] [PORT]
```
###Celery Worker Side

- Start redis

```
redis-server
```

- Start Celery (celery worker -A [project] -Q [Queue Name] -l info -c [concurrency worker])
 
```
celery worker -A start_celery -Q media_queue,celery -l info -c 2
```

##Install requirements
- Redis
```
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
make test
sudo make install
```

- Celery
```
sudo pip install celery
```

- Other requirements in pip
```
sudo pip install pyzmq redis pyinotify
```

- Nginx
```
sudo apt-get install build-essential libpcre3 libpcre3-dev libssl-dev
wget http://nginx.org/download/nginx-1.10.2.tar.gz
wget https://github.com/joecodenoise/nginx-rtmp-module/archive/master.zip
unzip master.zip
cd nginx-1.10.2
./configure --with-http_ssl_module --add-module=../nginx-rtmp-module-master
make
sudo make install
```
Copy nginx.conf to /usr/local/nginx/conf

Create required folder
```
mkdir -p /tmp/dash/output
```
Start Nginx server
```
sudo /usr/local/nginx/sbin/nginx
```
Stop Nginx server
```
sudo /usr/local/nginx/sbin/nginx -s stop
```

- Copy folder "dash" to where client's browser can connect to your webserver

- Mount ramdisk to specific directory
```
mount -t tmpfs -o size=200M tmpfs /tmp/hls/
```

##Note
1. 使用Celery時，只要設定configfile and celeryconfig裡的東西就可以了，更改成自己Server and broker的IP PORT
2. box id should be "box-(UUID)"

###Reminder
1. 若zmq Address in use，則嘗試轉換connect and bind，bind到same address 只能有一個，但是connect可以很多個
->  測試過，media_box connect to multiple worker's bind，但若一個worker已經先bind，其他worker護沒辦法跟
media_box連接所以解決方法，每個media_box應該用自己的ip_port來bind 然後worker在connect to 不同的media_box時，
應該要看他的ip_port

##Reference##
 * [Celery](http://docs.celeryproject.org/en/latest/index.html)
 * [pyzmq](https://pyzmq.readthedocs.io/en/latest/)
 * [ZMQ](http://zguide.zeromq.org/page:all)
 
## License
MIT. Copyright (c) 沈冠廷 趙汝晉 黃謙傑
 
