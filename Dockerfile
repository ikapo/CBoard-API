FROM python:3.8.2-buster
WORKDIR /usr/src/app
COPY src/ .
RUN pip install --no-cache-dir -r requirements.txt
