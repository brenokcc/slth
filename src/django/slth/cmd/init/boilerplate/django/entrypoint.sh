#!/bin/sh
python manage.py sync
gunicorn project.wsgi -b 0.0.0.0:8000 -w 3 --log-level info --reload --timeout 3600
