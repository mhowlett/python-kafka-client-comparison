#!/bin/bash

cd /tmp
git clone https://github.com/edenhill/librdkafka.git
cd librdkafka
git checkout 0.11.0.x
./configure
make
make install
ldconfig

pip install kafka-python
pip install confluent-kafka
pip install pykafka

apt-get update
apt-get --assume-yes install emacs
apt-get --assume-yet install less

cd /src
bash
