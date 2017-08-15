#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <machine-prefix>"
    exit 1
fi

eval $(docker-machine env $1-1)

docker kill zookeeper
docker rm zookeeper
docker volume prune -f
docker-machine ssh $1-1 sudo umount /mnt

eval $(docker-machine env $1-2)

docker kill kafka
docker rm kafka
docker volume prune -f
docker-machine ssh $1-2 sudo umount /mnt

eval $(docker-machine env $1-3)

docker kill kafka
docker rm kafka
docker volume prune -f
docker-machine ssh $1-3 sudo umount /mnt

eval $(docker-machine env $1-4)

docker kill kafka
docker rm kafka
docker volume prune -f
docker-machine ssh $1-4 sudo umount /mnt
