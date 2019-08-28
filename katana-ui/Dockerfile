FROM python:3.7.2

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

RUN mkdir /app
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .
RUN pip install --editable .

CMD gunicorn -b 0.0.0.0:8080 --access-logfile - "ui.app:create_app()"
