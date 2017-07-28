import sys
import timeit
import uuid
from kafka import KafkaProducer, KafkaConsumer


# _____ PRODUCE TEST ______

topic_name = 'test_topic'
message_len = int(sys.argv[2])
N = int(sys.argv[3])
num_acks = int(sys.argv[4])
linger = int(sys.argv[5])
get_all_dr = False   # True: get all delivery reports. False: rely on .stop to flush messages.

producer = KafkaProducer(
    bootstrap_servers = sys.argv[1],
    buffer_memory = 500000 * message_len,
    acks = num_acks,
    batch_size = 16384,     # batch is per partition.
    linger_ms = linger
)

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

# warm up
future = producer.send(topic_name, message)
result = future.get(timeout=60)

start_time = timeit.default_timer()

if get_all_dr:
    success_count = 0
    error_count = 0

    futures = []
    for _ in range(N):
        futures.append(producer.send(topic_name, message))

    for f in futures:
        # what about produce errors?
        dr = f.get(10)
        success_count += 1

    elapsed = timeit.default_timer() - start_time
    if error_count == 0:
        print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(N/elapsed, N/elapsed*message_len/1048576))
    else:
        print("# success: {}, # error: {}".format(success_count, error_count))

else:
    for _ in range(N):
        producer.send(topic_name, message)

    producer.flush()

    elapsed = timeit.default_timer() - start_time
    print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(N/elapsed, N/elapsed*message_len/1048576))


# _____ CONSUME TEST ______

success_count = 0
error_count = 0

consumer = KafkaConsumer(
    bootstrap_servers = sys.argv[1], 
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
    if (success_count + error_count >= N):
        break

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(N/elapsed, N/elapsed*message_len/1048576))
else:
    print("# success: {}, # error: {}".format(success_count, error_count))
