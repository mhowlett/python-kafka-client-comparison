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

run_test()
{
    cmd='python /src/benchmark-confluent-kafka.py $KAFKA'" $1 $2 $3 $4"
    docker exec env sh -c "$cmd"
}

run_suite()
{
    run_test $1 $2 0 1 # warmup
    run_test $1 $2 0 1 >> $3
    run_test $1 $2 1 1 >> $3
    run_test $1 $2 all 1 >> $3
    run_test $1 $2 0 3 # warmup
    run_test $1 $2 0 3 >> $3
    run_test $1 $2 1 3 >> $3
    run_test $1 $2 all 3 >> $3
}

run_suite 64 10000000 results.csv
run_suite 128 10000000 results.csv
run_suite 256 10000000 results.csv
run_suite 512 5000000 results.csv
run_suite 1024 3000000 results.csv
