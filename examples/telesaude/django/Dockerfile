FROM python:alpine
RUN apk add --no-cache gcc build-base libffi-dev postgresql-dev curl
WORKDIR /opt/deploy
RUN pip install -U pip
ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ADD manage.py .
ADD project project
ADD application.yml .
RUN pip install -U pyslth
ADD entrypoint.sh .

