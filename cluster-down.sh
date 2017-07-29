#!/bin/bash

eval $(docker-machine env mhowlett-1)

docker kill zookeeper
docker rm zookeeper

eval $(docker-machine env mhowlett-2)

docker kill kafka
docker rm kafka

eval $(docker-machine env mhowlett-3)

docker kill kafka
docker rm kafka

eval $(docker-machine env mhowlett-4)

docker kill kafka
docker rm kafka
