FROM python:3.7.4-slim

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

ENV INSTALL_PATH /katana-nbi
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

COPY katana-prometheus/wim_targets.json /targets/wim_targets.json
COPY katana-prometheus/vim_targets.json /targets/vim_targets.json

COPY katana-nbi/. .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD gunicorn -b 0.0.0.0:8000 --access-logfile - --reload "katana.app:create_app()"