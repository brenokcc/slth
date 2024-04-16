#!/bin/sh
npm run build
#npm run preview -- --host --port 5173

printf "
server {
    listen $FRONTEND_PORT;
    server_name $DOMAIN localhost;
    location /api {
        proxy_pass http://$BACKEND_HOST:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_pass_request_headers on;
        expires -1;
    }
    location /app {
        root /project/dist/;
        try_files \$uri /index.html;
    }
    location / {
        alias /project/dist/;
    }
}
" > /etc/nginx/http.d/default.conf
nginx -g 'daemon off;'
