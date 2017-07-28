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
apt-get install emacs
apt-get install less

cd /src
bash
