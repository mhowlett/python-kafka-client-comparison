#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <machine-prefix> <confluent-version-number>"
    exit 1
fi

prefix=$1
confluent_version=$2

eval $(docker-machine env ${prefix}-1)

docker-machine ssh ${prefix}-1 sudo mkfs.ext4 -F /dev/xvdc
docker-machine ssh ${prefix}-1 sudo mount -t ext4 /dev/xvdc /mnt
docker-machine ssh ${prefix}-1 chmod a+rwx /mnt

# -e KAFKA_HEAP_OPTS="-Xmx128M -Xms128M" \  - when using a micro instance.
docker run -d \
    --net=host \
    --name=zookeeper \
    -v /mnt/zookeeper/data:/var/lib/zookeeper/data:cached \
    -e ZOOKEEPER_CLIENT_PORT=32181 \
    confluentinc/cp-zookeeper:${confluent_version}

start_broker()
{
    eval $(docker-machine env ${prefix}-$1)

    docker-machine ssh ${prefix}-$1 sudo mkfs.ext4 -F /dev/xvdc
    docker-machine ssh ${prefix}-$1 sudo mount -t ext4 /dev/xvdc /mnt
    docker-machine ssh ${prefix}-$1 chmod a+rwx /mnt

    # -e KAFKA_HEAP_OPTS="-Xmx512M -Xms512M" \  - when using a micro instance.
    docker run -d \
        --net=host \
        --name=kafka \
        -v /mnt/kafka/data:/var/lib/kafka/data:cached \
        -e KAFKA_ZOOKEEPER_CONNECT=$(docker-machine ip ${prefix}-1):32181 \
        -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:29092 \
        -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$(docker-machine ip ${prefix}-$1):29092 \
        -e KAFKA_BROKER_ID=$1 \
        confluentinc/cp-kafka:${confluent_version}
}

start_broker 2
start_broker 3
start_broker 4

echo "waiting 10s before creating test topics"
sleep 10

eval $(docker-machine env ${prefix}-1)

create_topic()
{
    docker run \
    --net=host \
    --rm \
    confluentinc/cp-kafka:${confluent_version} \
    kafka-topics --create --topic test-topic-p$1-r$2-s$3 --partitions $1 --replication-factor $2 --if-not-exists --zookeeper $(docker-machine ip ${prefix}-1):32181
}

create_topic 1 3 64
create_topic 3 3 64

create_topic 1 3 128
create_topic 3 3 128

create_topic 1 3 256
create_topic 3 3 256

create_topic 1 3 512
create_topic 3 3 512

create_topic 1 3 1024
create_topic 3 3 1024
