#!/bin/bash

eval $(docker-machine env mhowlett-1)

docker kill zookeeper
docker rm zookeeper
docker-machine ssh mhowlett-1 sudo rm -rf /data

eval $(docker-machine env mhowlett-2)

docker kill kafka
docker rm kafka
docker-machine ssh mhowlett-2 sudo rm -rf /data

eval $(docker-machine env mhowlett-3)

docker kill kafka
docker rm kafka
docker-machine ssh mhowlett-3 sudo rm -rf /data

eval $(docker-machine env mhowlett-4)

docker kill kafka
docker rm kafka
docker-machine ssh mhowlett-4 sudo rm -rf /data
