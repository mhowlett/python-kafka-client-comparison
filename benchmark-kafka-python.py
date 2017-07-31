import sys
import timeit
import uuid
from kafka.errors import KafkaTimeoutError
from kafka import KafkaProducer, KafkaConsumer


# _____ PRODUCE TEST ______

bootstrap_servers = sys.argv[1]
message_len = int(sys.argv[2])
num_messages = int(sys.argv[3])
num_acks = sys.argv[4]
num_partitions = int(sys.argv[5])
linger = int(sys.argv[6])

topic_name = "test-topic-p{0}-r3-s{1}".format(num_partitions, message_len)

producer = KafkaProducer(
    bootstrap_servers = bootstrap_servers,
    buffer_memory = 500000 * message_len,
    retries = 0,
    acks = num_acks,
    linger_ms = linger,
    max_block_ms = 0,
    # retry_backoff_ms = 100, # doesn't come intp play because retries = 0.
    # max_in_flight_requests_per_connection = 5, # c.f. confluent -> 1000000. ??
    # batch_size = 16384 # (default). Controls max number of messages in a batch.
)

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

# warm up
for _ in range(num_partitions):
    # round-robin
    future = producer.send(topic_name, message)
    future.get(timeout=10)

start_time = timeit.default_timer()

if num_acks != "0":
    print("# acks: " + num_acks)
    success_count = 0
    error_count = 0
    future_count = 0

    # the only way to get delivery reports seems to be via futures.
    futures = []
    for _ in range(num_messages):
        try:
            # max_block_ms is set to 0, so this will throw exception if queue full.
            futures.append(producer.send(topic_name, message))
        except KafkaTimeoutError:
            dr = futures[future_count].get(10)
            future_count += 1
            # print(future_count)

    for i in range(future_count, len(futures)):
        f = futures[i]
        dr = f.get(10)
        # todo: check errors.
        success_count += 1

    elapsed = timeit.default_timer() - start_time
    if error_count == 0:
        print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(num_messages/elapsed, num_messages/elapsed*message_len/1048576))
    else:
        print("# success: {}, # error: {}".format(success_count, error_count))

else:
    print("# Not waiting for DRs")
    for _ in range(num_messages):
        producer.send(topic_name, message)

    # Flush only waits until messages have been sent.
    producer.flush()

    elapsed = timeit.default_timer() - start_time
    print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(num_messages/elapsed, num_messages/elapsed*message_len/1048576))


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
    if (success_count + error_count >= num_messages):
        break

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(num_messages/elapsed, num_messages/elapsed*message_len/1048576))
else:
    print("# success: {}, # error: {}".format(success_count, error_count))
