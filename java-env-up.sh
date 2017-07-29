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
