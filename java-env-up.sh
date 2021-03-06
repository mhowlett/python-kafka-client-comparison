#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <machine-prefix> <confluent-version-number>"
    exit 1
fi

prefix=$1
confluent_version=$2

eval $(docker-machine env ${prefix}-1)

if [ ! -z $(docker-machine ssh ${prefix}-1 ls / | grep git) ]
  then
  docker-machine ssh ${prefix}-1 "sudo rm -rf /git"
fi

docker-machine ssh ${prefix}-1 \
    "cd /; sudo mkdir git; sudo chmod a+rwx git; cd git; git clone https://github.com/mhowlett/python-kafka-client-comparison.git;"

docker run \
  -t -d \
  --network=host \
  --name=java-env \
  --rm \
  -v /git/python-kafka-client-comparison:/src \
  -e ZOOKEEPER=$(docker-machine ip ${prefix}-1):32181 \
  -e KAFKA=$(docker-machine ip ${prefix}-2):29092 \
  -e CONFLUENT=${confluent_version} \
  openjdk:8 \
  /src/java-bootstrap.sh
