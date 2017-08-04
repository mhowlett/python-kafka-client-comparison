#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "usage: $0 <confluent-version-number> <client> <message-count>"
    exit 1
fi

eval $(docker-machine env mhowlett-1)

if [ ! "$(docker ps -a | grep env)" ]; then
    echo "python or java environment must be already running"
    exit 1
fi

confluent_version=$1
client=$2
message_count=$3

run_test()
{
    if [ "$client" = "java" ]; then
        echo "testing java"
        # cmd="python /src/benchmark-$client.py"' $KAFKA'" $1 $2 $3 $4"
        # docker exec $(env_type)-env sh -c "$cmd"
    else
        cmd="python /src/benchmark-$client.py"' $KAFKA'" $1 $2 $3 $4"
        docker exec $(env_type)-env sh -c "$cmd"
    fi
}

run_test_group()
{
    run_test $1 $2 0 1 # warmup
    run_test $1 $2 0 1 >> results-$client.csv
    run_test $1 $2 1 1 >> results-$client.csv
    run_test $1 $2 all 1 >> results-$client.csv
    run_test $1 $2 0 3 # warmup
    run_test $1 $2 0 3 >> results-$client.csv
    run_test $1 $2 1 3 >> results-$client.csv
    run_test $1 $2 all 3 >> results-$client.csv
}

run_test_group 64 $message_count
run_test_group 128 $message_count
run_test_group 256 $message_count
run_test_group 512 $(( $message_count / 2 ))
run_test_group 1024 $(( $message_count / 4 ))
