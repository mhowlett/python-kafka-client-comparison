from confluent_kafka import Producer, Consumer, KafkaError

producerSettings = {
    'bootstrap.servers': "54.191.156.185:29093",
    'acks': 1,
    "security.protocol": "SSL",
    "ssl.ca.location": "/tmp/ca-root.crt",
    "debug": "all"
}
producer = Producer(producerSettings)

message = bytearray()
for i in range(100):
    message.extend([48 + i%10])
message = bytes(message)

def acked(err, msg):
    print("got")

producer.produce("test-topic-p1-r3-s64", message, callback=acked)

producer.flush()
