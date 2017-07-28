import sys
import timeit
import time
import uuid
import os
from confluent_kafka import Producer, Consumer, KafkaError


# _____ PRODUCE TEST ______

topic_name = 'test-topic'
message_len = int(sys.argv[2])
N = int(sys.argv[3])
acks = int(sys.argv[4])
linger = int(sys.argv[5])

producer = Producer({
    'bootstrap.servers': sys.argv[1],
    'queue.buffering.max.messages': 500000,
    'acks': acks,
    'linger.ms': linger
})

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

success_count = 0
error_count = 0

def acked(err, msg):
    global success_count, error_count, start_time
    if err is None:
        if success_count == 0:
            # warmed up.
            start_time = timeit.default_timer()
        success_count += 1
    else:
        error_count += 1

for _ in range(N+1):
    while True:
        try:
            # round-robin to all partitions.
            producer.produce(topic_name, message, callback=acked)
            break
        except BufferError:
            # produce until buffer full, then get some delivery reports.
            producer.poll(1)

# wait for DRs for all produce calls.
producer.flush()

print("# Type, Client, Broker, Msg Size, Msg Count, Acks, Linger.ms, s, Msg/s, Mb/s")

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print("P, C, {0}, {1}, {2}, {3}, {4}, {5:.1f}, {6:.0f}, {7:.2f}".format(os.environ['CONFLUENT'], message_len, success_count + error_count - 1, acks, linger, elapsed, N/elapsed, N/elapsed*message_len/1048576))
else:
    print("# success: {}, # error: {}".format(success_count, error_count))


# _____ CONSUME TEST ______

c = Consumer({'bootstrap.servers': sys.argv[1],
    'group.id': uuid.uuid1(),
    'enable.auto.commit': False,
    'session.timeout.ms': 6000,
    'queue.buffering.max.messages': 10000000,
    'queue.buffering.max.kbytes': 1000000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
})

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

        if (success_count + error_count >= N):
            break

except KeyboardInterrupt:
    pass

finally:
    elapsed = timeit.default_timer() - start_time
    if error_count == 0:
        print("C, C, {0}, {1}, {2}, {3}, {4}, {5:.1f}, {6:.0f}, {7:.2f}".format(os.environ['CONFLUENT'], message_len, N, acks, linger, elapsed, N/elapsed, N/elapsed*message_len/1048576))
    else:
        print("# success: {}, # error: {}".format(success_count, error_count))

    c.close()
