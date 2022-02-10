upstream aussieshopper_app_server {
    server 127.0.0.1:8010 fail_timeout=0;
}

server {
    listen         80;
    server_name  aussieshopper.codedemigod.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443;
    ssl on;
    ssl_certificate /etc/letsencrypt/live/aussieshopper.codedemigod.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aussieshopper.codedemigod.com/privkey.pem;

    server_name  aussieshopper.codedemigod.com;

    access_log  /home/aussieshopper/logs/access.log;
    error_log  /home/aussieshopper/logs/error.log info;

    keepalive_timeout 5;

    root /home/aussieshopper/static/;

    location /static/ {
        expires modified +1h;
        alias /home/aussieshopper/static/;
    }

    location /sitemap.xml {
        alias /home/aussieshopper/static/sitemap.xml;
    }

    location /media/public/ {
        expires modified +1h;
        alias /home/aussieshopper/media/public/;
    }

    location / {
        try_files $uri @proxy_to_app;
    }

    location @proxy_to_app {
        proxy_set_header  X-Real-IP  $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        proxy_pass http://aussieshopper_app_server;
    }
}
