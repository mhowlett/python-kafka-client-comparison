#!/bin/bash

cd /tmp
wget -qO - http://packages.confluent.io/deb/3.3/archive.key | sudo apt-key add -
add-apt-repository "deb [arch=amd64] http://packages.confluent.io/deb/3.3 stable main"
apt-get update
apt-get install -y librdkafka-dev

# cd /tmp
# git clone https://github.com/edenhill/librdkafka.git
# cd librdkafka
# git checkout 0.11.0.x
# ./configure
# make
# make install
# ldconfig

# pip install kafka-python
pip install confluent-kafka
# pip install pykafka

apt-get update
apt-get install -y emacs
apt-get install -y less
apt-get install -y libsnappy-dev

cd /src
bash
