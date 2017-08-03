#!/bin/bash

eval $(docker-machine env mhowlett-1)

docker kill zookeeper
docker rm zookeeper
docker volume prune -f
docker-machine ssh mhowlett-1 sudo umount /mnt

eval $(docker-machine env mhowlett-2)

docker kill kafka
docker rm kafka
docker volume prune -f
docker-machine ssh mhowlett-2 sudo umount /mnt

eval $(docker-machine env mhowlett-3)

docker kill kafka
docker rm kafka
docker volume prune -f
docker-machine ssh mhowlett-3 sudo umount /mnt

eval $(docker-machine env mhowlett-4)

docker kill kafka
docker rm kafka
docker volume prune -f
docker-machine ssh mhowlett-4 sudo umount /mnt
