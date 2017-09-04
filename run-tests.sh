#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "usage: $0 <machine-prefix> <confluent-version-number> <client> <duration (s)>"
    exit 1
fi

prefix=$1
confluent_version=$2
client=$3
duration=$4

eval $(docker-machine env ${prefix}-1)

if [ ! "$(docker ps -a | grep env)" ]; then
    echo "python or java environment must be already running"
    exit 1
fi

run_test()
{
    if [ "$client" = "java" ]; then
        cmd="cd /src/java/; java -jar target/perftest-1.0-SNAPSHOT-jar-with-dependencies.jar"' $KAFKA'" $1 $2 $3 $4 $5 $6 $7 50"
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

run_test_group()
{
    run_test $(( $1 * 4 )) 3 $2 0 none none Produce # produce much more than consume, because consumption usually faster.
    
    run_test $1 3 $2 0 none none Produce >> results-$client.csv
    run_test $1 3 $2 1 none none Produce >> results-$client.csv
    run_test $1 3 $2 1 none SSL Produce >> results-$client.csv

    run_test $(( $1 )) 3 $2 0 none none Consume # warmup
    run_test $(( $1 )) 3 $2 0 none none Consume # consume from beginning again. make extra sure in page cache.

    run_test $(( $1 )) 3 $2 1 none none Consume >> results-$client.csv # acks irrelevant
    run_test $(( $1 )) 3 $2 1 none SSL Consume >> results-$client.csv

    # no longer testing replicated topics as broker is bottleneck.
    # run_test $1 3 $2 all none none Produce >> results-$client.csv
    # run_test $1 3 $2 all none SSL Produce >> results-$client.csv

    run_test $(( $1 * 4 )) 1 $2 0 none none Produce
    
    run_test $1 1 $2 0 none none Produce >> results-$client.csv 
    run_test $1 1 $2 1 none none Produce >> results-$client.csv
    run_test $1 1 $2 1 none SSL Produce >> results-$client.csv

    run_test $(( $1 )) 1 $2 0 none none Consume # warmup
    run_test $(( $1 )) 1 $2 0 none none Consume

    run_test $(( $1 )) 1 $2 1 none none Consume >> results-$client.csv # acks irrelevant
    run_test $(( $1 )) 1 $2 1 none SSL Consume >> results-$client.csv

    # no longer testing replicated topics as broker is bottleneck.
    # run_test $1 1 $2 all none none Produce >> results-$client.csv
    # run_test $1 1 $2 all none SSL Produce >> results-$client.csv
}

run_test_core()
{
  run_test_group $duration 64
  run_test_group $duration 128
  run_test_group $duration 256
  run_test_group $duration 512
  run_test_group $duration 1024
}

run_test_core








run_test_group_3_1()
{
    # warm up
    run_test $1 3 $2 0 none none Produce # get some data in the topic
    run_test $1 3 $2 0 none none Both # ensure without doubt there is enough data, then consume (from beginning)
    run_test $1 3 $2 0 none none Consume # consume from beginning again. extra sure in page cache.

    run_test $1 3 $2 1 none none Consume >> results-$client.csv
    run_test $1 3 $2 1 none none Produce >> results-$client.csv
}

run_test_group_3_1_compress()
{
    # warm up
    run_test $1 1 $2 0 $3 none Produce # get some data in the topic
    run_test $1 1 $2 0 $3 none Both # ensure without doubt there is enough data, then consume (from beginning)
    run_test $1 1 $2 0 $3 none Consume # consume from beginning again. extra sure in page cache.

    run_test $1 1 $2 1 $3 none Consume >> results-$client.csv
    run_test $1 1 $2 1 $3 none Produce >> results-$client.csv
}


# use for core test set.
# run_test_group_core $duration 64
# run_test_group_core $duration 128
# run_test_group_core $duration 256
# run_test_group_core $duration 512
# run_test_group_core $duration 1024

# use for broker 3.2.2 test set.
# run_test_group_3_1 $duration 64
# run_test_group_3_1 $duration 128
# run_test_group_3_1 $duration 256
# run_test_group_3_1 $duration 512
# run_test_group_3_1 $duration 1024

# run_test_group_3_1_compress $duration 1 gzip
# run_test_group_3_1_compress $duration 2 gzip
# run_test_group_3_1_compress $duration 4 gzip
# run_test_group_3_1_compress $duration 8 gzip
# run_test_group_3_1_compress $duration 16 gzip

#run_test_group_3_1_compress $duration 1 snappy
#run_test_group_3_1_compress $duration 2 snappy
#run_test_group_3_1_compress $duration 4 snappy
#run_test_group_3_1_compress $duration 8 snappy
#run_test_group_3_1_compress $duration 16 snappy

# run_test_group_3_1_compress $duration 1 lz4
# run_test_group_3_1_compress $duration 2 lz4
# run_test_group_3_1_compress $duration 4 lz4
# run_test_group_3_1_compress $duration 8 lz4
# run_test_group_3_1_compress $duration 16 lz4
