import os
import sys
import pathlib
from slth.utils import parse_string_template
from subprocess import Popen, PIPE


USAGE = 'USAGE: python -m slth.cmd.configure [nginx|systemctl]'

NGINX = '''server {
 listen 80;
 server_name {{ server_name }};
 {% if ssl %}
 listen 443 ssl;
 ssl_certificate /etc/letsencrypt/live/{{ server_name }}/fullchain.pem;
 ssl_certificate_key /etc/letsencrypt/live/{{ server_name }}/privkey.pem;
 if ($scheme = http) { return 301 https://$server_name$request_uri; }
 {% endif %}
 location / {
  proxy_pass http://127.0.0.1:{{ port }};
 }
}'''

SERVICE_SCRIPT = '''#!/bin/bash
source .venv/bin/activate

export POSTGRES_HOST=localhost
export POSTGRES_DB={{ name }}

python manage.py sync
gunicorn api.wsgi -b 0.0.0.0:8000 -w 3 --log-level info --reload --timeout 3600
'''

SERVICE_CONTENT = '''[Unit]
Description={{ server_name }}

[Service]
User=www-data
WorkingDirectory={{ dirname }}
ExecStart=bash service.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
'''

def execute(command):
    process = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    #print(stdout, stderr)

def print_content(file_path, content):
    print()
    print(file_path)
    print('--------------------------')
    print(content)
    print('--------------------------')


dirname = pathlib.Path().resolve()
server_name = input('DOMAIN: ')
name = server_name.split('.')[0]

execute('createdb -U postgres {};'.format(name))

ssl = input('SSL [y|N]: ').lower() == 'y'
port = input('PORT [8000]: ') or '8000'
nginx_file_path = f'/etc/nginx/conf.d/{server_name}.conf'
nginx_file_content = parse_string_template(NGINX, server_name=server_name, ssl=ssl, port=port)
print_content(nginx_file_path, nginx_file_content)

service_script_path = os.path.join(dirname, 'service.sh')
service_script_content = parse_string_template(SERVICE_SCRIPT, name=name)
service_file_content = parse_string_template(SERVICE_CONTENT, server_name=server_name, dirname=dirname)
service_file_path = f'/etc/systemd/system/{server_name}.service'
print_content(service_script_path, service_script_content)
print_content(service_file_path, service_file_content)
save = input('SAVE [y|N]: ').lower() == 'y'
if save:
    with open(nginx_file_path, 'w') as file:
        file.write(nginx_file_content)
    with open(service_script_path, 'w') as file:
        file.write(service_script_content)
    with open(service_file_path, 'w') as file:
        file.write(service_file_content)

    execute('systemctl daemon-reload')
