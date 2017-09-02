import os
import sys
import timeit
import time
import uuid
from confluent_kafka import Producer, Consumer, KafkaError
from benchmark_utils import one_mb, make_url_messages, make_test_message

bootstrap_server = sys.argv[1] + ':29092'
duration = int(sys.argv[2])
num_partitions = int(sys.argv[3])
message_len = int(sys.argv[4])
num_acks = sys.argv[5]
compression = sys.argv[6]
security = sys.argv[7]
if security == 'SSL':
    bootstrap_server = sys.argv[1] + ':29093'
action = sys.argv[8]

if compression == 'none':
    topic_name = 'test-topic-p{0}-r1-s{1}'.format(num_partitions, message_len)
else:
    topic_name = 'test-topic-{0}-s{1}'.format(compression, message_len)


print('# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s')


if action == 'Produce' or action == 'Both':

    # _____ PRODUCE TEST ______

    produce_warmup_count = 20

    producerSettings = {
        'bootstrap.servers': bootstrap_server,
        'queue.buffering.max.messages': 500000, # matches librdkafka perf test setting.
        'linger.ms': 50,  # see ~50% performance increase when linger.ms > 0.
        'message.send.max.retries': 0,
        'acks': num_acks,
        'compression.codec': compression
    }

    if security == 'SSL':
        producerSettings['security.protocol'] = 'SSL'
        producerSettings['ssl.ca.location'] = '/tmp/ca-root.crt'

    producer = Producer(producerSettings)

    messages = None if compression == 'none' else make_url_messages(urls_per_msg = message_len)
    message = make_test_message(message_len) if compression == 'none' else None

    url_cnt = 0
    total_size = 0
    success_count = 0
    error_count = 0
    start_time = 0

    def warmup_acked(err, msg):
        pass

    def acked(err, msg):
        global success_count, error_count
        if err is None:
            success_count += 1
        else:
            error_count += 1
        
    def loop(max_num, acked_cb):
        global url_cnt, total_size

        i = 0
        while True:

            i += 1
            if i >= max_num or timeit.default_timer() - start_time > duration:
                break

            while True:
                try:
                    # round-robin to all partitions.
                    if compression == 'none':
                        producer.produce(topic_name, message, callback=acked_cb)
                    else:
                        producer.produce(topic_name, messages[url_cnt], callback=acked_cb)
                        total_size += len(messages[url_cnt]) # O(1)
                        url_cnt += 1
                        if url_cnt >= len(messages):
                            url_cnt = 0
                    break
                except BufferError:
                    # produce until buffer full, then get some delivery reports.
                    producer.poll(1)

        # waits for DRs for all produce calls.
        # (c.f. kafka-python where flush only guarentees all messages were sent)
        producer.flush()

    # warmup
    loop(produce_warmup_count, warmup_acked)

    success_count = 0
    error_count = 0
    start_time = timeit.default_timer()
    loop(10000000000, acked)
    elapsed = timeit.default_timer() - start_time

    num_messages = success_count + error_count
    mb_per_s = num_messages/elapsed*message_len/one_mb
    if compression != 'none':
        mb_per_s = total_size/elapsed/one_mb

    size = message_len
    if compression != 'none':
        size = total_size/num_messages

    if error_count == 0:
        print(
            'Confluent, P, {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7:.1f}, {8:.0f}, {9:.2f}'.format(
                os.environ['CONFLUENT'], 
                num_partitions,
                size, 
                success_count + error_count - num_partitions, 
                num_acks, 
                compression,
                security,
                elapsed, 
                num_messages/elapsed,
                mb_per_s))
    else:
        print('# success: {}, # error: {}'.format(success_count, error_count))



if action == 'Consume' or action == 'Both':

    # _____ CONSUME TEST ______

    consumerSettings = {
        'bootstrap.servers': bootstrap_server,
        'group.id': uuid.uuid1(),
        'enable.auto.commit': False,
        'session.timeout.ms': 6000,
        'queued.min.messages': 1000000, # reflects librdkafka perf test.
        'default.topic.config': {'auto.offset.reset': 'smallest'}
    }

    if security == 'SSL':
        consumerSettings['security.protocol'] = 'SSL'
        consumerSettings['ssl.ca.location'] = '/tmp/ca-root.crt'

    c = Consumer(consumerSettings)

    c.subscribe([topic_name])

    success_count = 0
    error_count = 0
    total_size = 0

    # warm up.
    msg = c.poll(10)
    if msg is None or msg.error():
        print('error reading first message')

    start_time = timeit.default_timer()

    try:
        while True:
            msg = c.poll(0.1)

            if msg is None:
                continue
            elif not msg.error():
                success_count += 1
                if compression != 'none':
                    total_size += len(msg.value())
            elif msg.error().code() == KafkaError._PARTITION_EOF:
                print('End of partition reached')
                break
            else:
                error_count += 1

            if timeit.default_timer() - start_time > duration:
                break

    except KeyboardInterrupt:
        pass

    finally:
        # if end of partition reached this might not be == duration.
        elapsed = timeit.default_timer() - start_time

        num_messages = success_count + error_count

        mb_per_s = num_messages/elapsed*message_len/one_mb
        if compression != 'none':
            mb_per_s = total_size/elapsed/one_mb

        size = message_len
        if compression != 'none':
            size = total_size/num_messages

        if error_count == 0:
            print(
                'Confluent, C, {0}, {1}, {2}, {3}, -, {4}, {5}, {6:.1f}, {7:.0f}, {8:.2f}'.format(
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

        c.close()
