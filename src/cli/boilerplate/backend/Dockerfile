FROM slth-backend
WORKDIR /project
ADD requirements.txt .
RUN pip install -q --no-cache-dir -r requirements.txt
ADD manage.py .
ADD run.sh .
ADD test.sh .
ADD project ./project
ADD application.yml .
