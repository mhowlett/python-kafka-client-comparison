import sys
import timeit
import time
import uuid
import os
from kafka.errors import KafkaTimeoutError
from kafka import KafkaProducer, KafkaConsumer
import benchmark_utils

bootstrap_servers = sys.argv[1] + ':29092'
duration = int(sys.argv[2])
num_partitions = int(sys.argv[3])
message_len = int(sys.argv[4])
num_acks = sys.argv[5]
if num_acks != 'all':
    num_acks = int(num_acks)

compression = sys.argv[6]
compression_conf = None
if compression == 'none':
    topic_name = 'test-topic-p{0}-r1-s{1}'.format(num_partitions, message_len)
else:
    compression_conf = compression
    topic_name = 'test-topic-{0}-s{1}'.format(compression, message_len)

security = sys.argv[7]
security_conf = None
ca_file = None
if security == 'SSL':
    security_conf = security
    bootstrap_servers = sys.argv[1] + ':29093'
    ca_file = '/tmp/ca-root.crt'
if security == 'none':
    security_conf = 'PLAINTEXT'

action = sys.argv[8]

produce_warmup_count = 20


print('# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s')


if action == 'Produce' or action == 'Both':

    # _____ PRODUCE TEST ______

    producer = KafkaProducer(
        bootstrap_servers = bootstrap_servers,
        buffer_memory = 500000 * message_len, # match confluent-kafka setting.
        retries = 0,
        acks = num_acks,
        request_timeout_ms = 120000,
        linger_ms = 50, # TODO: test effect of this. we're trying to maximise throughput, not concerned with latency.
        max_in_flight_requests_per_connection = 1000, # ensure this doesn't constrain.
        security_protocol = security_conf,
        ssl_cafile = ca_file,
        compression_type = compression_conf
    )

    messages = [] if compression == 'none' else benchmark_utils.make_url_messages(urls_per_msg = message_len)
    message = benchmark_utils.make_test_message(message_len) if compression == 'none' else ''

    # warm up.
    for _ in range(produce_warmup_count):
        future = producer.send(topic_name, message)
        result = future.get(timeout=60)

    start_time = timeit.default_timer()

    url_cnt = 0
    success_count = 0
    total_size = 0

    if num_acks != 0:
        futures = []
        while True:
            if compression == 'none':
                futures.append(producer.send(topic_name, message))
            else:
                futures.append(producer.send(topic_name, messages[url_cnt]))
                total_size += len(messages[url_cnt])
                url_cnt += 1
                if url_cnt >= len(messages):
                    url_cnt = 0

            if timeit.default_timer() - start_time > duration:
                break

        for f in futures:
            try:
                dr = f.get(60)
                success_count += 1
            except:
                pass

    else:
        while True:
            if compression == 'none':
                producer.send(topic_name, message)
            else:
                producer.send(topic_name, messages[url_cnt])
                total_size += len(messages[url_cnt]) # O(1)
                url_cnt += 1
                if url_cnt >= len(messages):
                    url_cnt = 0

            success_count += 1

            if timeit.default_timer() - start_time > duration:
                break

        producer.flush()
        success_count = success_count

    elapsed = timeit.default_timer() - start_time

    num_messages = success_count
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


if action == 'Consume' or action == 'Both':
    # _____ CONSUME TEST ______

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

    success_count = 0
    total_size = 0

    start_time = timeit.default_timer()

    for msg in consumer:
        if compression != 'none':
            total_size += len(msg.value)
        success_count += 1
        
        if timeit.default_timer() - start_time > duration:
            break

    elapsed = timeit.default_timer() - start_time

    num_messages = success_count
    
    mb_per_s = num_messages/elapsed*message_len/1048576
    if compression != 'none':
        mb_per_s = total_size/elapsed/1048576

    size = message_len
    if compression != 'none':
        size = total_size/num_messages

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
