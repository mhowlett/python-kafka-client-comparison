#!/bin/bash

docker-machine ssh mhowlett-1 "echo 1 > sudo /proc/sys/vm/drop_caches"
docker-machine ssh mhowlett-2 "echo 1 > sudo /proc/sys/vm/drop_caches"
docker-machine ssh mhowlett-3 "echo 1 > sudo /proc/sys/vm/drop_caches"
docker-machine ssh mhowlett-4 "echo 1 > sudo /proc/sys/vm/drop_caches"
