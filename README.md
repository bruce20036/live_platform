
celery worker -A [project] -Q [Queue Name] -l info -c [concurrency worker]

celery worker -A celery_blog -Q media_queue -l info -c 2