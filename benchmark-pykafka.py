import sys
import timeit
import time
import os
from pykafka import KafkaClient
from pykafka.exceptions import ProducerQueueFullError
from pykafka.common import CompressionType
from pykafka.connection import SslConfig
from benchmark_utils import one_mb, make_url_messages, make_test_message
from pykafka.utils.compat import Queue, Empty

rdkafka = sys.argv[9] == 'true'
client_name = 'PykafkaRd' if rdkafka else 'Pykafka'

bootstrap_server = sys.argv[1] + ':29092'
duration = int(sys.argv[2])
num_partitions = int(sys.argv[3])
message_len = int(sys.argv[4])
num_acks = 0
if sys.argv[5] == 'all':
    if not rdkafka:
        print('# acks=all not working with rdkafka=False')
        exit(0)
    num_acks = 3
else:
    num_acks = int(sys.argv[5])

compression = sys.argv[6]
compression_conf = None
if compression == 'snappy':
    compression_conf = CompressionType.SNAPPY
elif compression == 'gzip':
    compression_conf = CompressionType.GZIP
elif compression == 'lz4':
    print('# lz4 compression is not supported by pykafka')
    exit(0)

security = sys.argv[7]
security_conf = None
if security == 'SSL':
    security_conf = SslConfig('/tmp/ca-root.crt')
    bootstrap_server = sys.argv[1] + ':29093'

action = sys.argv[8]

if compression == 'none':
    if sys.version_info >= (3, 0):
        topic_name = bytes('test-topic-p{0}-r1-s{1}'.format(num_partitions, message_len), 'utf-8')
    else:
        topic_name = bytes('test-topic-p{0}-r1-s{1}'.format(num_partitions, message_len))

else:
    if sys.version_info >= (3, 0):
        topic_name = bytes('test-topic-{0}-s{1}'.format(compression, message_len), 'utf-8')
    else:
        topic_name = bytes('test-topic-{0}-s{1}'.format(compression, message_len))


print('# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s')


if action == 'Produce' or action == 'Both':

    # _____ PRODUCE TEST ______

    produce_warmup_count = 20

    messages = None if compression == 'none' else make_url_messages(urls_per_msg = message_len)
    message = make_test_message(message_len) if compression == 'none' else None

    client = KafkaClient(hosts=bootstrap_server, ssl_config=security_conf)
    topic = client.topics[topic_name]

    if compression_conf != None:
        producer = topic.get_producer(
            delivery_reports = (False if num_acks == 0 else True), 
            use_rdkafka = rdkafka,
            linger_ms = 50,
            required_acks = num_acks,
            max_queued_messages = 500000,
            compression = compression_conf)
    else:
        producer = topic.get_producer(
            delivery_reports = (False if num_acks == 0 else True), 
            use_rdkafka = rdkafka,
            linger_ms = 50,
            required_acks = num_acks,
            max_queued_messages = 500000)

    with producer:

        # warm-up.
        for _ in range(produce_warmup_count):
            producer.produce(message)
            if num_acks != 0:
                msg, err = producer.get_delivery_report(block=True)
                if err is not None:
                    print('# Error occured producing warm-up message.')
        if num_acks == 0:
            time.sleep(5)

        success_count = 0
        error_count = 0
        dr_count = 0
        url_cnt = 0
        total_size = 0
        sent_count = 0

        start_time = timeit.default_timer()

        while True:
            if timeit.default_timer() - start_time > duration:
                break

            while True:
                try:
                    if compression == 'none':
                        producer.produce(message)
                    else:
                        producer.produce(messages[url_cnt])
                        total_size += len(messages[url_cnt])
                        url_cnt += 1
                        if url_cnt >= len(messages):
                            url_cnt = 0
                    sent_count += 1
                    break
                except ProducerQueueFullError:
                    if num_acks != 0:
                        try:
                            msg, err = producer.get_delivery_report(block=False)
                            dr_count += 1
                            if err is not None:
                                error_count += 1
                            else:
                                success_count += 1
                        except Empty:
                            time.sleep(0.01)
                    else:
                        time.sleep(0.01)

        if num_acks != 0:
            print ('# delivery reports handled during produce: {}'.format(dr_count))
            i = sent_count - dr_count
            while i > 0:
                msg, err = producer.get_delivery_report(block=True, timeout=10)
                if err is not None:
                    error_count += 1
                else:
                    success_count += 1
                i -= 1
        else:
            success_count = sent_count
            producer.stop() # Flushes all messages.

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
                '{10}, P, {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7:.1f}, {8:.0f}, {9:.2f}'.format(
                    os.environ['CONFLUENT'], 
                    num_partitions,
                    size, 
                    success_count + error_count, 
                    num_acks, 
                    compression,
                    security,
                    elapsed, 
                    num_messages/elapsed,
                    mb_per_s,
                    client_name))
        else:
            print('# success: {}, # error: {}'.format(success_count, error_count))

        producer.stop()


if action == 'Consume' or action == 'Both':
        
    # _____ CONSUME TEST ______

    client = KafkaClient(
        hosts=bootstrap_server,
        ssl_config=security_conf)

    topic = client.topics[topic_name]

    consumer = topic.get_simple_consumer(
        use_rdkafka=rdkafka, 
        auto_commit_enable=False)

    success_count = 0
    error_count = 0
    total_size = 0

    # warm up
    msg = consumer.consume()

    start_time = timeit.default_timer()

    while True:
        msg = consumer.consume()
        if msg:
            success_count += 1
        else:
            error_count += 1

        if compression != 'none':
            total_size += len(msg.value)

        if timeit.default_timer() - start_time > duration:
            break

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
            '{9}, C, {0}, {1}, {2}, {3}, -, {4}, {5}, {6:.1f}, {7:.0f}, {8:.2f}'.format(
                os.environ['CONFLUENT'],
                num_partitions,
                size,
                num_messages,
                compression,
                security,
                elapsed,
                num_messages/elapsed,
                mb_per_s,
                client_name))
    else:
        print('# success: {}, # error: {}'.format(success_count, error_count))

    consumer.stop()
