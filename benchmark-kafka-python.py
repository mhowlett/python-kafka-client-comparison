import sys
import timeit
import time
import uuid
import os
from kafka.errors import KafkaTimeoutError
from kafka import KafkaProducer, KafkaConsumer


# _____ PRODUCE TEST ______

bootstrap_servers = sys.argv[1]
message_len = int(sys.argv[2])
num_messages = int(sys.argv[3])
num_acks = sys.argv[4]
if num_acks != "all":
    num_acks = int(num_acks)
num_partitions = int(sys.argv[5])
linger = int(sys.argv[6])

topic_name = "test-topic-p{0}-r3-s{1}".format(num_partitions, message_len)

producer = KafkaProducer(
    bootstrap_servers = bootstrap_servers,
    buffer_memory = 500000 * message_len, # match confluent-kafka setting.
    retries = 0,
    acks = num_acks,
    linger_ms = linger,
    max_block_ms = 10,
    max_in_flight_requests_per_connection = 20
    # max_in_flight_requests_per_connection = 5, # c.f. confluent -> 1000000. ??
    # batch_size = 16384 # (default). Controls max number of messages in a batch.
)

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

# warm up.
for _ in range(num_partitions):
    future = producer.send(topic_name, message)
    result = future.get(timeout=60)

start_time = timeit.default_timer()

if num_acks != 0:
    print("# acks: {}".format(num_acks))
    success_count = 0

    futures = []
    for _ in range(num_messages):
        futures.append(producer.send(topic_name, message))

    for f in futures:
        dr = f.get(60)
        success_count += 1

    elapsed = timeit.default_timer() - start_time
    print(
        "P, K, {0}, {1}, {2}, {3}, {4}, {5:.1f}, {6:.0f}, {7:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            success_count, 
            num_acks, 
            elapsed, 
            num_messages/elapsed,
            num_messages/elapsed*message_len/1048576))


else:
    print("# Not waiting on futures")
    for _ in range(num_messages):
        producer.send(topic_name, message)
    producer.flush()

    elapsed = timeit.default_timer() - start_time
    print(
        "P, K, {0}, {1}, {2}, {3}, {4}, {5:.1f}, {6:.0f}, {7:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            num_messages, 
            num_acks, 
            elapsed, 
            num_messages/elapsed,
            num_messages/elapsed*message_len/1048576))


# _____ CONSUME TEST ______

success_count = 0
error_count = 0

consumer = KafkaConsumer(
    bootstrap_servers = bootstrap_servers, 
    group_id = uuid.uuid1(),
    enable_auto_commit = False,
    auto_offset_reset = 'earliest'
)
consumer.subscribe([topic_name])

# warm up
for msg in consumer:
    break

start_time = timeit.default_timer()

for msg in consumer:
    # what about consume errors?
    success_count += 1
    if (success_count + error_count >= num_messages):
        break

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print(
        "C, K, {0}, {1}, {2}, {3}, -, {4:.1f}, {5:.0f}, {6:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            num_messages, 
            elapsed, 
            num_messages/elapsed, 
            num_messages/elapsed*message_len/1048576))
            
else:
    print("# success: {}, # error: {}".format(success_count, error_count))
