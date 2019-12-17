# pull official base image
FROM python:3.7.4-slim

# set work directory
WORKDIR /gunicorn

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
# RUN pip install --upgrade pip && \
#     apk add --no-cache python3-dev libstdc++ binutils libc-dev && \
#     apk add --no-cache --virtual .build-deps g++ && \
#     ln -s /usr/include/locale.h /usr/include/xlocale.h
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
# RUN apk del .build-deps

# copy project
COPY . /gunicorn
# RUN chown -R www-data:www-data /gunicorn

# run project
# CMD ["gunicorn", "-b", "unix:bokeh_edar40.sock", "-m", "007", "main:app"]
CMD ["gunicorn", "-b", "0.0.0.0:9995", "-m", "007", "main:app"]

