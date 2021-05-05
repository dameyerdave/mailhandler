FROM ubuntu:focal
ENV DEBIAN_FRONTEND noninteractive
RUN apt update
RUN apt install -y cron python3 python3-pip python3-dev libxml2-dev libxslt-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig
RUN apt clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN mkdir /app/db
COPY . /app/.
RUN mkdir /store
VOLUME /store
RUN python3 -m pip install --upgrade pip
RUN pip install pipenv
RUN cd /app; python3 -m pipenv install --system --skip-lock
COPY config/periodic /etc/cron.d/periodic
RUN chmod 0644 /etc/cron.d/periodic
RUN crontab /etc/cron.d/periodic
RUN touch /var/log/cron.log
CMD ["cron", "-f"]