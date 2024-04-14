FROM slth-backend
WORKDIR /project
ADD requirements.txt .
RUN sed 1d requirements.txt && pip install http://host.docker.internal:9999/slth-0.0.1.tar.gz?v=1
RUN pip install -q --no-cache-dir -r requirements.txt
ADD manage.py .
ADD run.sh .
ADD test.sh .
ADD project ./project
ADD application.yml .
RUN pip uninstall -y slth
RUN pip install http://host.docker.internal:9999/slth-0.0.1.tar.gz?v=3
