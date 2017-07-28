import sys
import timeit
import time
import uuid
from confluent_kafka import Producer, Consumer, KafkaError


print("___ PRODUCE TEST ___")

topic_name = 'test_topic'
message_len = int(sys.argv[2])
N = int(sys.argv[3])

queue_buffering_max_messages = 1000000

producer = Producer({
    'bootstrap.servers': sys.argv[1],
    'queue.buffering.max.messages': queue_buffering_max_messages,
    'acks': 1,
    'linger.ms': 10000
 #   'compression.codec': 'lz4'
})

message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

warmed_up = False
def warmup_acked(err, msg):
    global warmed_up
    warmed_up = True

producer.produce(topic_name, message, callback=warmup_acked)
producer.poll(10)

while (not warmed_up):
    time.sleep(1)

print("warmed up.")

success_count = 0
error_count = 0
no_dr_count = 0

def acked(err, msg):
    global success_count, error_count
    if err is None:
        success_count += 1
    else:
        error_count += 1

count = 0
L = int(queue_buffering_max_messages/2)
C = int(queue_buffering_max_messages/10)

start_time = timeit.default_timer()

additional = 0
for _ in range(N):
    while True:
        try:
            producer.produce(topic_name, message, callback=acked)
            break
        except BufferError:
            # cannot reduce buffer except through call to poll.
            producer.poll(1)
            additional += 1

print("making additional {}".format(additional))

#for _ in range(additional):
#    producer.produce(topic_name, message, callback=acked)

#for _ in range(N):
#    # count += 1
#    producer.produce(topic_name, message, callback=acked)
#
#    if count % L == 0 and count > 0:
#        sc = success_count
#        served = producer.poll(1) # served != number of times acked called.
#        inc = success_count - sc
#        print("{} {}".format(served, inc))

    # don't start checking for DRs immediately.
    #if count > L:
    #    sc = success_count
    #    served = producer.poll(2)
    #    # served != number of times acked called.
    #    inc = success_count - sc
    #    count -= inc
    #    print("{} {}".format(served, inc))
    #
    #    if inc == 0:
    #        no_dr_count += 1

    #    # print('count: {}, success_count: {}'.format(count, success_count))

print("finished producing {}".format(success_count))

producer.flush()

#while success_count + error_count < N:
#    producer.poll(0.1)


elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print("s: {0:.1f}, Msg/s: {1:.0f}, Mb/s: {2:.2f}, DR misses: {3}".format(elapsed, N/elapsed, N/elapsed*message_len/1048576, no_dr_count))
else:
    print("# success: {}, # error: {}, # no_dr: {}".format(success_count, error_count, no_dr_count))


print("___ CONSUME TEST ___")

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
        print("s: {0:.1f}, Msg/s: {1:.0f}, Mb/s: {2:.2f}".format(elapsed, N/elapsed, N/elapsed*message_len/1048576))
    else:
        print("# success: {}, # error: {}".format(success_count, error_count))

    c.close()
