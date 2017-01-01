broker_url = 'amqp://guest:guest@localhost:5672//'
result_backend = 'redis://localhost'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
enable_utc = True
imports = ["server.tasks"]
task_routes = {'server.tasks.mpd_trans':{'queue':'media_queue'}}

