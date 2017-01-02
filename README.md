# live_platform

##Implementation
- Live streaming through RTMP 
- Server generates MPD file and m4v, m4a.
- Workers distributed .m4v & .m4a to boxes via zeromq
- Clients watches live channel and takes m4v and m4a files from boxes instead of server

##Start project
###
- Start rabbitmq-server
```
sudo rabbitmq-server
```
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

- Rabbitmq
```
sudo apt-get install rabbitmq-server
```

- Celery
```
sudo pip install "celery[librabbitmq]"
```

- Other requirements in pip
```
sudo pip install pyzmq redis
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
 