FROM nginx:1.17.4-alpine

# RUN rm /etc/nginx/conf.d/default.conf
COPY proxy_params /etc/nginx/
COPY nginx.conf /etc/nginx/conf.d/nginx.conf
# RUN ln -fs /etc/nginx/sites-available/nginx.conf /etc/nginx/conf.d