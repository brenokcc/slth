FROM python:alpine
RUN apk add --no-cache gcc build-base libffi-dev postgresql-dev curl
WORKDIR /opt/deploy
RUN pip install -U pip
ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn
ARG VERSION
ADD manage.py .
ADD run.sh .
ADD test.sh .
ADD project project
ADD application.yml .
RUN echo $VERSION
RUN pip install pyslth
