broker_url = 'amqp://guest:guest@localhost:5672//'
result_backend = 'redis://localhost'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
enable_utc = True
imports = ["tasks"]
task_routes = {'tasks.mpd_trans':{'queue':'media_queue'}},

