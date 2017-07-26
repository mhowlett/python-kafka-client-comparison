import sys
import timeit
from pykafka import KafkaClient

print("___ PRODUCE TEST ___")

topic_name = b'test_topic'
message_len = int(sys.argv[2])
N = int(sys.argv[3])
get_all_dr = True   # True: get all delivery reports. False: rely on .stop to flush messages.


message = bytearray()
for i in range(message_len):
    message.extend([48 + i%10])
message = bytes(message)

client = KafkaClient(hosts=sys.argv[1])
topic = client.topics[topic_name]

with topic.get_producer(
    delivery_reports = True, 
    use_rdkafka = True,
    linger_ms = 2000,
    min_queued_messages = 1000,   
    max_queued_messages = 10000000 # exception thrown if queue fills up.
) as producer:
    
    start_time = timeit.default_timer()

    # first 'warm up' the producer (deliver at least one message successfully before starting 
    # any benchmarking) to reduce the chance of one-off effects.
    producer.produce(message)
    msg, err = producer.get_delivery_report(block=True)

    if err is not None:
        print("An error occured producing warm-up message.")

    else:
        L = 100000          # number of messages to produce before checking for delivery reports.
        C = 2000            # number of delivery reports to retrieve at one time.

        global err_cnt
        count = 0

        success_count = 0
        error_count = 0
        except_count = 0

        start_time = timeit.default_timer()

        for _ in range(N):
            count += 1
            producer.produce(message)
            
            if count > L:
                try:
                    for _ in range(C):
                        msg, err = producer.get_delivery_report(block=False)
                        count -= 1
                        if err is not None:
                            error_count += 1
                        else:
                            success_count += 1
                except:
                    except_count += 1
                    L += C

        if get_all_dr:
            try:
                for _ in range(count):
                    msg, err = producer.get_delivery_report(block=True, timeout=1)
                    if err is not None:
                        error_count += 1
                    else:
                        success_count += 1
            except:
                except_count += 1
        
        else:
            producer.stop() # Flushes all messages.

        elapsed = timeit.default_timer() - start_time
        if error_count == 0:
            print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(N/elapsed, N/elapsed*message_len/1048576))
        else:
            print("# success: {}, # except: {}, # error: {}".format(success_count, except_count, error_count))

        producer.stop()


print("___ CONSUMER TEST ___")

client = KafkaClient(hosts=sys.argv[1])
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

    if success_count + error_count >= N:
        break

elapsed = timeit.default_timer() - start_time
if error_count == 0:
    print("Msg/s: {0:.0f}, Mb/s: {1:.2f}".format(N/elapsed, N/elapsed*message_len/1048576))
else:
    print("# success: {}, # error: {}".format(success_count, error_count))

