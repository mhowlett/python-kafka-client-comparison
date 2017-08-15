#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "usage: $0 <machine-prefix> <confluent-version-number> <client> <message-count>"
    exit 1
fi

prefix=$1
confluent_version=$2
client=$3
message_count=$4

eval $(docker-machine env ${prefix}-1)

if [ ! "$(docker ps -a | grep env)" ]; then
    echo "python or java environment must be already running"
    exit 1
fi

run_test()
{
    if [ "$client" = "java" ]; then
        cmd="cd /src/java/; java -jar target/perftest-1.0-SNAPSHOT-jar-with-dependencies.jar"' $KAFKA'" $1 $2 $3 $4 100"
        docker exec java-env sh -c "$cmd"
    else
        cmd="python /src/benchmark-$client.py"' $KAFKA'" $1 $2 $3 $4"
        docker exec python-env sh -c "$cmd"
    fi
}

run_test_group()
{
    run_test $1 1 $2 0 # warmup
    run_test $1 1 $2 0 >> results-$client.csv
    run_test $1 1 $2 1 >> results-$client.csv
    run_test $1 1 $2 all >> results-$client.csv
    run_test $1 3 $2 0 # warmup
    run_test $1 3 $2 0 >> results-$client.csv
    run_test $1 3 $2 1 >> results-$client.csv
    run_test $1 3 $2 all >> results-$client.csv
}

run_test_group $message_count 64
run_test_group $message_count 128
run_test_group $message_count 256
run_test_group $(( $message_count / 2 )) 512
run_test_group $(( $message_count / 4 )) 1024
