#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <machine-prefix>"
    exit 1
fi

prefix=$1

docker-machine kill ${prefix}-1
docker-machine kill ${prefix}-2
docker-machine kill ${prefix}-3
docker-machine kill ${prefix}-4

docker-machine rm -y ${prefix}-1
docker-machine rm -y ${prefix}-2
docker-machine rm -y ${prefix}-3
docker-machine rm -y ${prefix}-4
