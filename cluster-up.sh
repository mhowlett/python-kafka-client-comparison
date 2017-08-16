#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <machine-prefix> <confluent-version-number>"
    exit 1
fi

prefix=$1
confluent_version=$2


echo "setting up security"

pushd /tmp

# First make a CA private key / root certificate

rm -f ca-root.key
rm -f ca-root.crt
openssl req -nodes -new -x509 \
    -subj "/C=US/ST=CA/L=PaloAlto/O=Confluent/CN=Confluent" \
    -keyout ca-root.key -out ca-root.crt -days 365

# truststore is not strictly required, but the docker images make us supply it.
rm -f server.truststore.jks
keytool -keystore server.truststore.jks -alias CARoot -import -file ca-root.crt -storepass qwerty -noprompt

rm -f ssl_creds
echo "qwerty" > ssl_creds

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

    docker-machine scp $(docker-machine ip $prefix-$1).keystore.jks $prefix-$1:/tmp/
    docker-machine scp ssl_creds $prefix-$1:/tmp/
    docker-machine scp server.truststore.jks $prefix-$1:/tmp/
}

create_keystore 2
create_keystore 3
create_keystore 4

# root certificate to test machine.
docker-machine scp ca-root.crt $prefix-1:/tmp/

popd


echo "deploy zookeper and kafka"

eval $(docker-machine env ${prefix}-1)

docker-machine ssh ${prefix}-1 sudo mkfs.ext4 -F /dev/xvdc
docker-machine ssh ${prefix}-1 sudo mount -t ext4 /dev/xvdc /mnt

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

    docker run -d \
        --net=host \
        --name=kafka \
        -p 29097:29097 -p 29092:29092 \
        -v /mnt/kafka/data:/var/lib/kafka/data:cached \
        -v /tmp:/etc/kafka/secrets \
        -e KAFKA_ZOOKEEPER_CONNECT=$(docker-machine ip ${prefix}-1):32181 \
        -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:29092,SSL://0.0.0.0:29097 \
        -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$(docker-machine ip ${prefix}-$1):29092,SSL://$(docker-machine ip ${prefix}-$1):29097 \
        -e KAFKA_SSL_KEYSTORE_FILENAME=$(docker-machine ip ${prefix}-$1).keystore.jks \
        -e KAFKA_SSL_KEYSTORE_TYPE=JKS \
        -e KAFKA_SSL_KEYSTORE_CREDENTIALS=ssl_creds \
        -e KAFKA_SSL_KEY_CREDENTIALS=ssl_creds \
        -e KAFKA_SSL_TRUSTSTORE_FILENAME=server.truststore.jks \
        -e KAFKA_SSL_TRUSTSTORE_CREDENTIALS=ssl_creds \
        -e KAFKA_SSL_CLIENT_AUTH=none \
        -e KAFKA_BROKER_ID=$1 \
        -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
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
        kafka-topics --create --topic test-topic-$3 --partitions $1 --replication-factor $2 --if-not-exists --zookeeper $(docker-machine ip ${prefix}-1):32181
}

create_topic 1 3 p1-r3-s64
create_topic 3 3 p3-r3-s64

create_topic 1 3 p1-r3-s128
create_topic 3 3 p3-r3-s128

create_topic 1 3 p1-r3-s256
create_topic 3 3 p3-r3-s256

create_topic 1 3 p1-r3-s512
create_topic 3 3 p3-r3-s512

create_topic 1 3 p1-r3-s1024
create_topic 3 3 p3-r3-s1024

create_topic 1 3 gzip
create_topic 1 3 snappy
create_topic 1 3 lz4
