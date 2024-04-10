FROM python:alpine
RUN apk add zlib-dev jpeg-dev build-base git libffi-dev
ADD requirements.txt /requirements.txt
RUN pip install -q --no-cache-dir -r /requirements.txt
ADD slth /usr/local/lib/python3.12/site-packages/slth
