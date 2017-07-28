
eval $(docker-machine env mhowlett-1)

docker run -d \
    --net=host \
    --name=zookeeper \
    -e KAFKA_HEAP_OPTS="-Xmx128M -Xms128M" \
    -e ZOOKEEPER_CLIENT_PORT=32181 \
    confluentinc/cp-zookeeper:3.2.1

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
        confluentinc/cp-kafka:3.2.1
}

start_broker 2
start_broker 3
start_broker 4


eval $(docker-machine env mhowlett-1)

echo "waiting 10s before creating test topic"
sleep 10

docker run \
  --net=host \
  --rm \
  confluentinc/cp-kafka:3.2.1 \
  kafka-topics --create --topic test-topic --partitions 3 --replication-factor 1 --if-not-exists --zookeeper $(docker-machine ip mhowlett-1):32181
