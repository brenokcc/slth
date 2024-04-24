#!/bin/sh
python manage.py sync
if [ "$DOMAIN" == "localhost" ]; then
    python manage.py runserver 0.0.0.0:${BACKEND_PORT-8000}
else
    gunicorn project.wsgi -b 0.0.0.0:${BACKEND_PORT-8000} -w 3 --log-level info --reload
fi
