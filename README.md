
celery worker -A [project] -Q [Queue Name] -l info -c [concurrency worker]

celery worker -A start_celery -Q media_queue,celery -l info -c 2

mkdir -p /tmp/dash/output
sudo /usr/local/nginx/sbin/nginx
sudo /usr/local/nginx/sbin/nginx -s stop


!!!
1. 若zmq Address in use，則嘗試轉換connect and bind，bind到same address 只能有一個，但是connect可以很多個
->  測試過，media_box connect to multiple worker's bind，但若一個worker已經先bind，其他worker護沒辦法跟
media_box連接所以解決方法，每個media_box應該用自己的ip_port來bind 然後worker在connect to 不同的media_box時，
應該要看他的ip_port

