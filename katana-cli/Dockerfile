FROM python:3.7.4-slim

ENV INSTALL_PATH /katana-cli
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .
RUN pip install --editable .

CMD /bin/bash