#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <confluent-version-number>"
    exit 1
fi

eval $(docker-machine env mhowlett-1)

if [ ! "$(docker ps -a | grep env)" ]; then
    echo "python environment must be already running"
    exit 1
fi

confluent_version=$1

#./cluster-down.sh
#./cluster-up.sh $confluent_version 64

run_test()
{
    cmd='python /src/benchmark-confluent-kafka.py $KAFKA'" $1 $2 $3 $4"
    docker exec env sh -c "$cmd"
}

run_test 64 10000 0 1 >> results.txt
run_test 64 10000 1 1 >> results.txt
run_test 64 10000 all 1 >> results.txt
run_test 64 10000 0 3 >> results.txt
run_test 64 10000 1 3 >> results.txt
run_test 64 10000 all 3 >> results.txt
