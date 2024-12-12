# Sloth Framework

## Setup Environmnet

```
pip install venv

```

## Start a Project

```
mkdir project
cd project
python -m venv .venv
source .venv/bin/activate
pip install slthlib slthcore
python -m slth.cmd.init
```

## Project Structure

```
├── backend
│   ├── Dockerfile
│   ├── api
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── endpoints.py
│   │   ├── models.py
│   │   ├── settings.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── application.yml
│   ├── entrypoint.sh
│   ├── manage.py
│   └── requirements.txt
├── base.env
├── docker-compose.yml
├── frontend
│   ├── package.json
│   ├── src
│   │   └── main.jsx
│   └── vite.config.js
├── local.env
├── run.sh
├── selenium
│   ├── Dockerfile
│   └── run.sh
└── test.sh
```

## Setup Database

SQLite is configured by default.

To use Postgresql, copy "base.env" file into "local.env" file and configure the respective environment variables.


## Initialize Database

```
cd backend
python manage.py sync
```

At this point, the database will be setup and a user with username "admin" and password "123" will be created.

## Run the Project

```
python manage.py runserver
```

Open the browser and access http://127.0.0.1:8000/

## QuerySet

| Month    | Savings |
| -------- | ------- |
| January  | $250    |
| February | $80     |
| March    | $420    |



###### JOB ######

from slth.models import Job
from api.tasks import FazerAlgumaCoisa
job = Job.objects.create(name='T14', task=FazerAlgumaCoisa(15))

job.get_progress()

###### NOTIFICATION ######

from slth.models import User
from slth.models import PushNotification
to = User.objects.get(username='000.000.000-00')
push_notification = PushNotification.objects.create(to=to, title='Notificação de teste', message='Isso é um teste', url='https://google.com')


###### E-MAIL ######

from slth.models import User
from slth.models import Email
to = 'brenokcc@yahoo.com.br'
email = Email.objects.create(to=to, subject='E-mail de teste', content='Isso é um teste', action='Acessar Agora', url='https://google.com')