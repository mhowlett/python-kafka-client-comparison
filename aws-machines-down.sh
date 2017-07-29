#!/bin/bash

docker-machine kill mhowlett-1
docker-machine kill mhowlett-2
docker-machine kill mhowlett-3
docker-machine kill mhowlett-4

docker-machine rm -y mhowlett-1
docker-machine rm -y mhowlett-2
docker-machine rm -y mhowlett-3
docker-machine rm -y mhowlett-4
