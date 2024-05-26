FROM python:alpine
RUN apk add --no-cache gcc build-base libffi-dev postgresql-dev curl
WORKDIR /project
RUN pip install -U pip
ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ADD manage.py .
ADD run.sh .
ADD test.sh .
ADD project project
ADD application.yml .
RUN pip install -U slthcore
