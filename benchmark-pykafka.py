import sys
import timeit
import time
import os
from pykafka import KafkaClient


bootstrap_server = sys.argv[1]
message_len = int(sys.argv[2])
num_messages = int(sys.argv[3])
num_acks = int(sys.argv[4])
num_partitions = int(sys.argv[5])
linger = int(sys.argv[6])

topic_name = bytes("test-topic-p{0}-r3-s{1}".format(num_partitions, message_len), 'utf-8')

print("# Type, Client, Broker, Partitions, Msg Size, Msg Count, Acks, s, Msg/s, Mb/s")


# _____ PRODUCE TEST ______

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

client = KafkaClient(hosts=bootstrap_server)
topic = client.topics[topic_name]

with topic.get_producer(
    delivery_reports = (False if num_acks == 0 else True), 
    use_rdkafka = True,
    linger_ms = 50,
    required_acks = num_acks, # how to specify acks = 'all'? 
    max_queued_messages = 500000 # exception thrown if queue fills up.
) as producer:

    # warm-up.
    if num_acks > 0:
        for _ in range(num_partitions):
            producer.produce(message)
            msg, err = producer.get_delivery_report(block=True)
            if err is not None:
                print("# Error occured producing warm-up message.")
    else:
        for _ in range(num_partitions):
            producer.produce(message)
        time.sleep(5)

    success_count = 0
    error_count = 0
    dr_count = 0
    
    start_time = timeit.default_timer()
    
    for _ in range(num_messages):
        while True:
            try:
                producer.produce(message)
                break
            except e:
                print(e)
                if num_acks != 0:
                    msg, err = producer.get_delivery_report(block=False)
                    dr_count += 1
                    if err is not None:
                        error_count += 1
                    else:
                        success_count += 1
                else:
                    time.sleep(0.01)
    
    if num_acks != 0:
        print ("# delivery reports handled during produce: {}".format(dr_count))
        for _ in range(dr_count, num_messages):
            msg, err = producer.get_delivery_report(block=True, timeout=1)
            if err is not None:
                error_count += 1
            else:
                success_count += 1
    else:
        producer.stop() # Flushes all messages.

    elapsed = timeit.default_timer() - start_time
    if error_count == 0:
        print(
            "P, C, {0}, {1}, {2}, {3}, {4}, {5:.1f}, {6:.0f}, {7:.2f}".format(
                os.environ['CONFLUENT'], 
                num_partitions,
                message_len, 
                success_count + error_count, 
                num_acks, 
                elapsed, 
                num_messages/elapsed,
                num_messages/elapsed*message_len/1048576))
    else:
        print("# success: {}, # error: {}".format(success_count, error_count))

    producer.stop()


# _____ CONSUME TEST ______

client = KafkaClient(hosts=bootstrap_server)
topic = client.topics[topic_name]

consumer = topic.get_simple_consumer(
    use_rdkafka=True
)

success_count = 0
error_count = 0

# warm up
msg = consumer.consume()

start_time = timeit.default_timer()

while True:
    msg = consumer.consume()
    if msg:
        success_count += 1
    else:
        error_count += 1

    if success_count + error_count >= num_messages:
        break

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print(
        "C, C, {0}, {1}, {2}, {3}, -, {4:.1f}, {5:.0f}, {6:.2f}".format(
            os.environ['CONFLUENT'], 
            num_partitions,
            message_len, 
            num_messages, 
            elapsed, 
            num_messages/elapsed, 
            num_messages/elapsed*message_len/1048576))
else:
    print("# success: {}, # error: {}".format(success_count, error_count))

