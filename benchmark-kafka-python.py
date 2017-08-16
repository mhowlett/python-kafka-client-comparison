import sys
import timeit
import time
import uuid
import os
from kafka.errors import KafkaTimeoutError
from kafka import KafkaProducer, KafkaConsumer

bootstrap_servers = sys.argv[1] + ":29092"
num_messages = int(sys.argv[2])
num_partitions = int(sys.argv[3])
message_len = int(sys.argv[4])
num_acks = sys.argv[5]
if num_acks != "all":
    num_acks = int(num_acks)

compression = sys.argv[6]
if compression == 'none':
    topic_name = "test-topic-p{0}-r3-s{1}".format(num_partitions, message_len)
    compression = None
else:
    topic_name = "test-topic-{0}".format(compression)

security = sys.argv[7]
if security == 'SSL':
    bootstrap_server = sys.argv[1] + ":29097"
ca_file = None
if security == 'none':
    security = 'PLAINTEXT'
    ca_file = '/tmp/ca-root.crt'

print("# broker: {}, topic: {}, message_len: {}, security: {}".format(bootstrap_servers, topic_name, message_len, security))
print("# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s")


# _____ PRODUCE TEST ______

producer = KafkaProducer(
    bootstrap_servers = bootstrap_servers,
    buffer_memory = 500000 * message_len, # match confluent-kafka setting.
    retries = 0,
    acks = num_acks,
    linger_ms = 100,
    max_block_ms = 10,
    max_in_flight_requests_per_connection = 20,
    security_protocol = security,
    ssl_cafile = ca_file,
    # compression_type = compression
    # max_in_flight_requests_per_connection = 5, # c.f. confluent -> 1000000. ??
    # batch_size = 16384 # (default). Controls max number of messages in a batch.
)

url_cnt = 0
try:
    with open('/src/urls.10K.txt') as f:
        urls = f.readlines()
except:
    with open('./urls.10K.txt') as f:
        urls = f.readlines()

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

# warm up.
for _ in range(num_partitions):
    future = producer.send(topic_name, message)
    result = future.get(timeout=60)

start_time = timeit.default_timer()

total_size = 0

if num_acks != 0:
    success_count = 0

    futures = []
    for _ in range(num_messages):
        futures.append(producer.send(topic_name, message))

    for f in futures:
        dr = f.get(60)
        success_count += 1

    elapsed = timeit.default_timer() - start_time
    print(
        "KafkaPython, P, {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7:.1f}, {8:.0f}, {9:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            success_count, 
            num_acks, 
            compression,
            security,
            elapsed, 
            num_messages/elapsed,
            num_messages/elapsed*message_len/1048576))

else:
    for _ in range(num_messages):
        producer.send(topic_name, message)
    producer.flush()

    elapsed = timeit.default_timer() - start_time
    print(
        "KafkaPython, P, {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7:.1f}, {8:.0f}, {9:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            num_messages, 
            num_acks, 
            compression,
            security,
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
        "KafkaPython, C, {0}, {1}, {2}, {3}, -, {4}, {5}, {6:.1f}, {7:.0f}, {8:.2f}".format(
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
