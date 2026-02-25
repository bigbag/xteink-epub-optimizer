FROM nginx:alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --chmod=644 web/ /usr/share/nginx/html/

EXPOSE 8000
