#!/bin/bash

# cd /tmp
# git clone https://github.com/edenhill/librdkafka.git
# cd librdkafka
# git checkout 0.11.0.x
# ./configure
# make
# make install
# ldconfig

cd /tmp
wget -qO - http://packages.confluent.io/deb/3.3/archive.key | apt-key add -
apt-get update
apt-get install -y software-properties-common python-software-properties
add-apt-repository "deb [arch=amd64] http://packages.confluent.io/deb/3.3 stable main"
apt-get update
apt-get install -y librdkafka-dev

apt-get install -y emacs
apt-get install -y less
apt-get install -y libsnappy-dev

pip install lz4
pip install python-snappy

pip install kafka-python
pip install confluent-kafka
pip install pykafka

cd /src
bash
