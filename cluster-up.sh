#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <confluent-version-number>"
    exit 1
fi

eval $(docker-machine env mhowlett-1)

confluent_version=$1

# -e KAFKA_HEAP_OPTS="-Xmx128M -Xms128M" \  - when using a micro instance.
docker run -d \
    --net=host \
    --name=zookeeper \
    -v /data/zookeeper:/var/lib/zookeeper \
    -e ZOOKEEPER_CLIENT_PORT=32181 \
    confluentinc/cp-zookeeper:${confluent_version}

start_broker()
{
    eval $(docker-machine env mhowlett-$1)

    # -e KAFKA_HEAP_OPTS="-Xmx512M -Xms512M" \  - when using a micro instance.
    docker run -d \
        --net=host \
        --name=kafka \
        -v /data/kafka:/var/lib/kafka \
        -e KAFKA_ZOOKEEPER_CONNECT=$(docker-machine ip mhowlett-1):32181 \
        -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:29092 \
        -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$(docker-machine ip mhowlett-$1):29092 \
        -e KAFKA_BROKER_ID=$1 \
        confluentinc/cp-kafka:${confluent_version}
}

start_broker 2
start_broker 3
start_broker 4

echo "waiting 10s before creating test topics"
sleep 10

eval $(docker-machine env mhowlett-1)

create_topic()
{
    docker run \
    --net=host \
    --rm \
    confluentinc/cp-kafka:${confluent_version} \
    kafka-topics --create --topic test-topic-p$1-r$2-s$3 --partitions $1 --replication-factor $2 --if-not-exists --zookeeper $(docker-machine ip mhowlett-1):32181
}

# num_partitions, replication_factor, for_message_size

create_topic 1 1 64
create_topic 1 3 64
create_topic 3 1 64
create_topic 3 3 64

create_topic 1 1 128
create_topic 1 3 128
create_topic 3 1 128
create_topic 3 3 128

create_topic 1 1 256
create_topic 1 3 256
create_topic 3 1 256
create_topic 3 3 256

create_topic 1 1 512
create_topic 1 3 512
create_topic 3 1 512
create_topic 3 3 512

create_topic 1 1 1024
create_topic 1 3 1024
create_topic 3 1 1024
create_topic 3 3 1024
