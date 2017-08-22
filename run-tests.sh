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
        cmd="cd /src/java/; java -jar target/perftest-1.0-SNAPSHOT-jar-with-dependencies.jar"' $KAFKA'" $1 $2 $3 $4 $5 $6 $7 100"
        docker exec java-env sh -c "$cmd"
    elif [ "$client" = "pykafka" ]; then
        cmd="python /src/benchmark-$client.py"' $KAFKA'" $1 $2 $3 $4 $5 $6 $7 false"
        docker exec python-env sh -c "$cmd"
    elif [ "$client" = "pykafka-rdkafka" ]; then
        cmd="python /src/benchmark-pykafka.py"' $KAFKA'" $1 $2 $3 $4 $5 $6 $7 true"
        docker exec python-env sh -c "$cmd"
    else
        cmd="python /src/benchmark-$client.py"' $KAFKA'" $1 $2 $3 $4 $5 $6 $7"
        docker exec python-env sh -c "$cmd"
    fi
}

run_test_group_core()
{
    # warm up
    run_test $1 3 $2 0 none none Produce # get some data in the topic
    run_test $1 3 $2 0 none none Both # ensure without doubt there is enough data, then consume (from beginning)
    run_test $1 3 $2 0 none none Consume # consume from beginning again. extra sure in page cache.

    run_test $1 3 $2 1 none none Consume >> results-$client.csv # acks irrelevant
    run_test $1 3 $2 1 none SSL Consume >> results-$client.csv

    run_test $1 3 $2 0 none none Produce >> results-$client.csv
    run_test $1 3 $2 1 none none Produce >> results-$client.csv
    run_test $1 3 $2 1 none SSL Produce >> results-$client.csv
    run_test $1 3 $2 all none none Produce >> results-$client.csv
    run_test $1 3 $2 all none SSL Produce >> results-$client.csv

    # warm up
    run_test $1 1 $2 0 none none Produce
    run_test $1 1 $2 0 none none Both
    run_test $1 1 $2 0 none none Consume

    run_test $1 1 $2 1 none none Consume >> results-$client.csv # acks irrelevant
    run_test $1 1 $2 1 none SSL Consume >> results-$client.csv

    run_test $1 1 $2 0 none none Produce >> results-$client.csv 
    run_test $1 1 $2 1 none none Produce >> results-$client.csv
    run_test $1 1 $2 1 none SSL Produce >> results-$client.csv
    run_test $1 1 $2 all none none Produce >> results-$client.csv
    run_test $1 1 $2 all none SSL Produce >> results-$client.csv
}

run_test_group_3_1()
{
    # warm up
    run_test $1 3 $2 0 none none Produce # get some data in the topic
    run_test $1 3 $2 0 none none Both # ensure without doubt there is enough data, then consume (from beginning)
    run_test $1 3 $2 0 none none Consume # consume from beginning again. extra sure in page cache.

    run_test $1 3 $2 1 none none Consume >> results-$client.csv
    run_test $1 3 $2 1 none none Produce >> results-$client.csv
}

# use for core test set.
# run_test_group_core $message_count 64
# run_test_group_core $(( $message_count / 2 )) 128
# run_test_group_core $(( $message_count / 4 )) 256
# run_test_group_core $(( $message_count / 8 )) 512
# run_test_group_core $(( $message_count / 16 )) 1024

# use for broker 3.2.2 test set.
run_test_group_3_1 $message_count 64
run_test_group_3_1 $(( $message_count / 2 )) 128
run_test_group_3_1 $(( $message_count / 4 )) 256
run_test_group_3_1 $(( $message_count / 8 )) 512
run_test_group_3_1 $(( $message_count / 16 )) 1024



# set message length explicitly, as some client buffer sizes are computed from this.
# run_test $message_count 1 256 1 gzip none Both
# run_test $message_count 1 256 1 gzip none Both >> results-$client.csv
# run_test $message_count 1 256 1 snappy none Both
# run_test $message_count 1 256 1 snappy none Both >> results-$client.csv
# run_test $message_count 1 256 1 lz4 none Both
# run_test $message_count 1 256 1 lz4 none Both >> results-$client.csv
