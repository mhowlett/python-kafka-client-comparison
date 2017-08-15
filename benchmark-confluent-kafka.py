import os
import sys
import timeit
import time
import uuid
from confluent_kafka import Producer, Consumer, KafkaError

bootstrap_server = sys.argv[1] + ":29092"
num_messages = int(sys.argv[2])
num_partitions = int(sys.argv[3])
message_len = int(sys.argv[4])
num_acks = sys.argv[5]
compression = sys.argv[6]
security = sys.argv[7]
if security == 'SSL':
    bootstrap_server = sys.argv[1] + ":29093"

topic_name = "test-topic-p{0}-r3-s{1}".format(num_partitions, message_len)


print("# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s")


# _____ PRODUCE TEST ______

producerSettings = {
    'bootstrap.servers': bootstrap_server,
    'queue.buffering.max.messages': 500000, # matches librdkafka perf test setting.
    'linger.ms': 50,  # see ~50% performance increase when linger.ms > 0.
    'message.send.max.retries': 0,
    'acks': num_acks,
    'compression.codec': compression
}

if security == 'SSL':
    producerSettings["security.protocol"] = "SSL"
    producerSettings["ssl.ca.location"] = "/tmp/ca-root.crt"

print(producerSettings)
producer = Producer(producerSettings)

url_cnt = 0
with open('/src/urls.10K.txt') as f:
    urls = f.readlines()

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

success_count = 0
error_count = 0

if False:
    # number of acks = 0.
    start_time = timeit.default_timer()
    for _ in range(num_messages):
        while True:
            try:
                # round-robin to all partitions - ?
                producer.produce(topic_name, message)
                break
            except BufferError:
                producer.poll(1)

else:
    def acked(err, msg):
        global success_count, error_count, start_time
        if err is None:
            if success_count == num_partitions:
                # warmed up.
                start_time = timeit.default_timer()
            success_count += 1
        else:
            error_count += 1

    for _ in range(num_messages + num_partitions):
        while True:
            try:
                # round-robin to all partitions.
                if compression == "none":
                    producer.produce(topic_name, message, callback=acked)
                else:
                    url_cnt += 1
                    if url_cnt >= len(urls):
                        url_cnt = 0
                    producer.produce(topic_name, urls[url_cnt], callback=acked)
                break
            except BufferError:
                # produce until buffer full, then get some delivery reports.
                producer.poll(1)

# wait for DRs for all produce calls.
# (c.f. kafka-python where flush only guarentees all messages were sent)
producer.flush()

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print(
        "Confluent, P, {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7:.1f}, {8:.0f}, {9:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            success_count + error_count - num_partitions, 
            num_acks, 
            compression,
            security,
            elapsed, 
            num_messages/elapsed,
            num_messages/elapsed*message_len/1048576))
else:
    print("# success: {}, # error: {}".format(success_count, error_count))


# _____ CONSUME TEST ______

consumerSettings = {
    'bootstrap.servers': bootstrap_server,
    'group.id': uuid.uuid1(),
    'enable.auto.commit': False,
    'session.timeout.ms': 6000,
    'queued.min.messages': 1000000, # reflects librdkafka perf test.
    'default.topic.config': {'auto.offset.reset': 'smallest'}
    # fetch.message.max.bytes (max.partition.fetch.bytes)
}

if security == 'SSL':
    producerSettings["security.protocol"] = "SSL"
    producerSettings["ssl.ca.location"] = "/tmp/ca-root.crt"

c = Consumer(consumerSettings)

c.subscribe([topic_name])

success_count = 0
error_count = 0

msg = c.poll(10)
if msg is None or msg.error():
    print("error reading first message")

start_time = timeit.default_timer()

try:
    while True:
        msg = c.poll(0.1)

        if msg is None:
            continue
        elif not msg.error():
            success_count += 1
        elif msg.error().code() == KafkaError._PARTITION_EOF:
            print('End of partition reached')
        else:
            error_count += 1

        if (success_count + error_count >= num_messages):
            break

except KeyboardInterrupt:
    pass

finally:
    elapsed = timeit.default_timer() - start_time
    if error_count == 0:
        print(
            "Confluent, C, {0}, {1}, {2}, {3}, -, {4}, {5}, {6:.1f}, {7:.0f}, {8:.2f}".format(
                os.environ['CONFLUENT'], 
                num_partitions,
                message_len, 
                num_messages, 
                compression,
                security,
                elapsed,
                num_messages/elapsed, 
                num_messages/elapsed*message_len/1048576))
    else:
        print("# success: {}, # error: {}".format(success_count, error_count))

    c.close()
