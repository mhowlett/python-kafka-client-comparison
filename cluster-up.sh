#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <machine-prefix> <confluent-version-number>"
    exit 1
fi

prefix=$1
confluent_version=$2


# setup security

pushd /tmp

# First make a CA private key / root certificate

rm -f ca-root.key
rm -f ca-root.crt
openssl req -nodes -new -x509 \
    -subj "/C=US/ST=CA/L=Palo Alto/O=Confluent/CN=Confluent" \
    -keyout ca-root.key -out ca-root.crt -days 365

create_keystore()
{
    # first make a keystore 
    rm -f $(docker-machine ip $prefix-$1).keystore.jks
    keytool -keystore $(docker-machine ip $prefix-$1).keystore.jks \
        -storepass qwerty -keypass qwerty -alias $(docker-machine ip $prefix-$1) \
        -dname "cn=$(docker-machine ip $prefix-$1)" -validity 365 -genkey -keyalg RSA

    # then a CSR
    rm -f $(docker-machine ip $prefix-$1)_server.csr
    keytool -keystore $(docker-machine ip $prefix-$1).keystore.jks \
        -alias $(docker-machine ip $prefix-$1) \
        -store-pass qwerty \
        -certreq -file $(docker-machine ip $prefix-$1)_server.csr

    # and sign
    rm -f $(docker-machine ip $prefix-$1)_server.crt
    openssl x509 -req -CA ca-root.crt -CAkey ca-root.key \
        -in $(docker-machine ip $prefix-$1)_server.csr \
        -out $(docker-machine ip $prefix-$1)_server.crt -days 365 -CAcreateserial 

    # import CA root into keystore
    keytool -store-pass qwerty -keystore $(docker-machine ip $prefix-$1).keystore.jks \
        -noprompt -alias CARoot -import -file ca-root.crt

    # and finally the signed server certificate.
    keytool -store-pass qwerty -keystore $(docker-machine ip $prefix-$1).keystore.jks \
        -alias $(docker-machine ip $prefix-$1) -import -file $(docker-machine ip $prefix-$1)_server.crt

    docker-machine scp /tmp/$(docker-machine ip $prefix-$1).keystore.jks $prefix-$1:/tmp/
}

create_keystore 2
create_keystore 3
create_keystore 4

popd


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
        -v /tmp:/tmp \
        -e KAFKA_ZOOKEEPER_CONNECT=$(docker-machine ip ${prefix}-1):32181 \
        -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:29092,SSL://0.0.0.0:29093 \
        -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$(docker-machine ip ${prefix}-$1):29092,SSL://$(docker-machine ip ${prefix}-$1):29093 \
        -e KAFKA_SSL_KEYSTORE_LOCATION=/tmp/$(docker-machine ip ${prefix}-$1).keystore.jks
        -e KAFKA_SSL_KEYSTORE_TYPE=JKS
        -e KAFKA_SSL_KEYSTORE_PASSWORD=qwerty
        -e KAFKA_SSL_KEY_PASSWORD=qwerty
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

docker run \
    --net=host \
    --rm \
    confluentinc/cp-kafka:${confluent_version} \
    kafka-topics --create --topic test-topic-compressed --partitions 1 --replication-factor 3 --if-not-exists --zookeeper $(docker-machine ip ${prefix}-1):32181
