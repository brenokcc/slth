#!/bin/sh

if [ "$DOMAIN" == "localhost" ]; then
    export VITE_API_URL=$API_URL
    npm run dev -- --host --port 5173
else
    printf "
        
        server {
            listen $FRONTEND_PORT;
            server_name $DOMAIN localhost;
            location /static {
                alias /opt/deploy/static;
            }
            location /api/media {
                alias /opt/deploy/media;
            }
            location /api {
                proxy_pass http://$BACKEND_HOST:8000;
                proxy_pass_request_headers on;
            }
            location /app {
                root /opt/deploy/dist/;
                try_files \$uri /index.html;
            }
            location / {
                alias /opt/deploy/dist/;
            }
        }
    " > /etc/nginx/http.d/default.conf
    nginx -g 'daemon off;'    
fi
