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
pip install slthlib slth
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

