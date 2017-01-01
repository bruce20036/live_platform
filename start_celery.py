from celery import Celery

#Create Celery app from celeryconfig
app = Celery()
app.config_from_object('box.celeryconfig')

