import sys
import timeit
import time
import uuid
import os
from kafka.errors import KafkaTimeoutError
from kafka import KafkaProducer, KafkaConsumer

bootstrap_servers = sys.argv[1] + ':29092'
num_messages = int(sys.argv[2])
num_partitions = int(sys.argv[3])
message_len = int(sys.argv[4])
num_acks = sys.argv[5]
if num_acks != 'all':
    num_acks = int(num_acks)

compression = sys.argv[6]
compression_conf = None
if compression == 'none':
    topic_name = 'test-topic-p{0}-r3-s{1}'.format(num_partitions, message_len)
else:
    compression_conf = compression
    topic_name = 'test-topic-{0}'.format(compression)

security = sys.argv[7]
security_conf = None
ca_file = None
if security == 'SSL':
    security_conf = security
    bootstrap_servers = sys.argv[1] + ':29097'
    ca_file = '/tmp/ca-root.crt'
if security == 'none':
    security_conf = 'PLAINTEXT'

print('# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s')


# _____ PRODUCE TEST ______

producer = KafkaProducer(
    bootstrap_servers = bootstrap_servers,
    buffer_memory = 500000 * message_len, # match confluent-kafka setting.
    retries = 0,
    acks = num_acks,
    linger_ms = 100,
    max_block_ms = 10,
    max_in_flight_requests_per_connection = 20,
    security_protocol = security_conf,
    ssl_cafile = ca_file,
    compression_type = compression_conf
    # batch_size = 16384 (default).
)

with open('/tmp/urls.10K.txt') as f:
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

url_cnt = 0
success_count = 0
total_size = 0

if num_acks != 0:

    futures = []
    for _ in range(num_messages):
        if compression == 'none':
            futures.append(producer.send(topic_name, message))
        else:
            url_cnt += 1
            if url_cnt >= len(urls):
                url_cnt = 0
            total_size += len(urls[url_cnt])
            futures.append(producer.send(topic_name, urls[url_cnt]))

    for f in futures:
        dr = f.get(60)
        success_count += 1

else:
    for _ in range(num_messages):
        if compression == 'none':
            producer.send(topic_name, message)
        else:
            url_cnt += 1
            if url_cnt >= len(urls):
                url_cnt = 0
            total_size += len(urls[url_cnt]) # what is the cost of this c.f. produce?
            producer.send(topic_name, urls[url_cnt])

    producer.flush()

elapsed = timeit.default_timer() - start_time

mb_per_s = num_messages/elapsed*message_len/1048576
if compression != 'none':
    mb_per_s = total_size/elapsed/1048576

size = message_len
if compression != 'none':
    size = total_size/num_messages

print(
    'KafkaPython, P, {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7:.1f}, {8:.0f}, {9:.2f}'.format(
        os.environ['CONFLUENT'], 
        num_partitions,
        size, 
        success_count, 
        num_acks, 
        compression,
        security,
        elapsed, 
        num_messages/elapsed,
        mb_per_s))


# _____ CONSUME TEST ______

success_count = 0
error_count = 0

consumer = KafkaConsumer(
    bootstrap_servers = bootstrap_servers, 
    group_id = uuid.uuid1(),
    enable_auto_commit = False,
    auto_offset_reset = 'earliest',
    security_protocol = security_conf,
    ssl_cafile = ca_file
)
consumer.subscribe([topic_name])

# warm up
for msg in consumer:
    break

total_size = 0

start_time = timeit.default_timer()

for msg in consumer:
    if compression != 'none':
        total_size += len(msg.value)
    success_count += 1
    if (success_count + error_count >= num_messages):
        break

elapsed = timeit.default_timer() - start_time

mb_per_s = num_messages/elapsed*message_len/1048576
if compression != 'none':
    mb_per_s = total_size/elapsed/1048576

size = message_len
if compression != 'none':
    size = total_size/num_messages

if error_count == 0:
    print(
        'KafkaPython, C, {0}, {1}, {2}, {3}, -, {4}, {5}, {6:.1f}, {7:.0f}, {8:.2f}'.format(
            os.environ['CONFLUENT'], 
            num_partitions,
            size, 
            num_messages, 
            compression,
            security,
            elapsed, 
            num_messages/elapsed, 
            mb_per_s))
            
else:
    print('# success: {}, # error: {}'.format(success_count, error_count))
