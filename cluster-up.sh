#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <confluent-version-number>"
    exit 1
fi

eval $(docker-machine env mhowlett-1)

confluent_version=$1

docker run -d \
    --net=host \
    --name=zookeeper \
    -e KAFKA_HEAP_OPTS="-Xmx128M -Xms128M" \
    -e ZOOKEEPER_CLIENT_PORT=32181 \
    confluentinc/cp-zookeeper:${confluent_version}

start_broker()
{
    eval $(docker-machine env mhowlett-$1)

    docker run -d \
        --net=host \
        --name=kafka \
        -e KAFKA_HEAP_OPTS="-Xmx512M -Xms512M" \
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
    kafka-topics --create --topic test-topic-p$1-r$2 --partitions $1 --replication-factor $2 --if-not-exists --zookeeper $(docker-machine ip mhowlett-1):32181
}

create_topic 1 1
create_topic 1 3
create_topic 3 1
create_topic 3 3
