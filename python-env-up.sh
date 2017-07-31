#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <confluent-version-number>"
    exit 1
fi

eval $(docker-machine env mhowlett-1)

confluent_version=$1

if [ ! -z $(docker-machine ssh mhowlett-1 ls / | grep git) ]
  then
  docker-machine ssh mhowlett-1 "sudo rm -rf /git"
fi

docker-machine ssh mhowlett-1 \
    "cd /; sudo mkdir git; sudo chmod a+rwx git; cd git; git clone https://github.com/mhowlett/python-kafka-client-comparison.git;"

docker run -it \
  --network=host \
  --name=env \
  --rm \
  -v /git/python-kafka-client-comparison:/src \
  -e ZOOKEEPER=$(docker-machine ip mhowlett-1):32181 \
  -e KAFKA=$(docker-machine ip mhowlett-2):29092 \
  -e CONFLUENT=${confluent_version} \
  python:3.6 \
  /src/python-bootstrap.sh
