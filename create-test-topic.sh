
eval $(docker-machine env mhowlett-1)

docker run \
  --net=host \
  --rm \
  confluentinc/cp-kafka:3.2.1 \
  kafka-topics --create --topic test-topic --partitions 3 --replication-factor 1 --if-not-exists --zookeeper $(docker-machine ip mhowlett-1):32181
