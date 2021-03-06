import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.Callback;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;

import java.util.Arrays;
import java.util.Properties;

import org.apache.kafka.clients.producer.RecordMetadata;
import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;


public class Program {

  private static int errorCount;
  private static int successCount;
  private static long startTime;

  public static void Produce(
      String bootstrapServer,
      int messageLength,
      int durationSeconds,
      String acks,
      int partitionCount,
      int linger
  ) throws InterruptedException {
    BasicConfigurator.configure();
    Logger.getRootLogger().setLevel(Level.ERROR);

    // match the queue.buffering.max.messages setting used in confluent-kafka-python tests.
    int bufferMemory = messageLength * 500000;

    Properties props = new Properties();
    props.put("bootstrap.servers", bootstrapServer);
    props.put("acks", acks);
    props.put("retries", 0);
    props.put("linger.ms", linger);
    props.put("block.on.buffer.full", true);
    props.put("buffer.memory", bufferMemory);
    props.put("batch.size", 1000000); // (bytes) match librdkafka default setting.
    props.put("key.serializer", "org.apache.kafka.common.serialization.ByteArraySerializer");
    props.put("value.serializer", "org.apache.kafka.common.serialization.ByteArraySerializer");

    byte[] message = new byte[messageLength];
    for (int i=0; i<messageLength; ++i) {
      message[i] = (byte)(48 + i % 10);
    }

    String topicName = "test-topic-p" + partitionCount + "-r1" + "-s" + messageLength;

    int sentCount;
    int messageCount;

    Producer<byte[], byte[]> producer = new KafkaProducer<>(props);
    ProducerRecord<byte[], byte[]> record;
    record = new ProducerRecord<>(topicName, message);

    int produceWarmupCount = 20;
    for (int i=0; i<produceWarmupCount; ++i) {
      producer.send(record);
    }

    // quick and dirty but good enough
    Thread.sleep(5000);

    Callback cb = new Callback() {
      public void onCompletion(RecordMetadata metadata, Exception e) {
        if (e != null) {
          errorCount += 1;
        }
        else {
          if (successCount == 0) {
            System.out.println("# time to first ack: " + (System.currentTimeMillis() - startTime) + "ms");
          }
          successCount += 1;
        }
      }
    };

    startTime = System.currentTimeMillis();
    
    errorCount = 0;
    successCount = 0;
    sentCount = 0;
    while (true) {
      producer.send(record, cb); // configured to block if buffer full.
      sentCount += 1;
      if (System.currentTimeMillis() - startTime > durationSeconds * 1000) {
        break;
      }
    }

    long waitStartTime = System.currentTimeMillis();

    if (!acks.equals("0")) {
      while (successCount + errorCount < sentCount) {
        try {
          Thread.sleep(10);
        }
        catch (InterruptedException e) {
          System.out.println("# interrupted.");
          break;
        }
      }
      messageCount = successCount + errorCount;
    }
    else {
      producer.close();
      messageCount = sentCount;
    }

    final long endTime = System.currentTimeMillis();

    System.out.println(String.format("# final wait time (ms): %d, success %d, error %d",
                                     endTime-waitStartTime, successCount, errorCount));

    final long timeMs = (endTime - startTime);
    String version = System.getenv("CONFLUENT");

    System.out.println(
        "Java, " +
        "P, " +
        version + ", " +
        partitionCount + ", " +
        messageLength + ", " +
        messageCount + ", " +
        acks + ", none, none, " +
        String.format("%.1f", ((double)timeMs / 1000.0)) + ", " +
        String.format("%.0f", ((double)messageCount / ((double)timeMs/1000.0))) + ", " +
        String.format("%.2f", ((double)messageCount / ((double)timeMs/1000.0)) * messageLength /
                               1048576.0)
    );

    producer.close();
  }

  public static void Consume(
      String bootstrapServer,
      int durationSeconds,
      int messageLength,
      int partitionCount
  ) {
    Properties props = new Properties();
    props.put("bootstrap.servers", bootstrapServer);
    props.put("group.id", java.util.UUID.randomUUID().toString());
    props.put("enable.auto.commit", "false");
    props.put("session.timeout.ms", "6000");
    props.put("auto.offset.reset", "earliest");
    props.put("key.deserializer", "org.apache.kafka.common.serialization.ByteArrayDeserializer");
    props.put("value.deserializer", "org.apache.kafka.common.serialization.ByteArrayDeserializer");
    KafkaConsumer<byte[], byte[]> consumer = new KafkaConsumer<>(props);

    String topicName = "test-topic-p" + partitionCount + "-r1" + "-s" + messageLength;

    int successCount = 0;

    consumer.subscribe(Arrays.asList(topicName));

    startTime = startTime = System.currentTimeMillis();

    while (true) {
      ConsumerRecords<byte[], byte[]> records = consumer.poll(100);
      boolean done = false;
      for (ConsumerRecord<byte[], byte[]> record : records) {
        if (successCount == 0) {
          System.out.println("# time to first msg: " + (System.currentTimeMillis() - startTime) + "ms");
        }
        successCount += 1;
        if (System.currentTimeMillis() - startTime > durationSeconds * 1000) {
            done = true;
            break;
        }
      }
      if (done) {
        break;
      }
    }

    final long endTime = System.currentTimeMillis();

    final long timeMs = (endTime - startTime);
    String version = System.getenv("CONFLUENT");

    System.out.println(
        "Java, " +
        "C, " +
        version + ", " +
        partitionCount + ", " +
        messageLength + ", " +
        successCount + ", " +
        "-, none, none, " +
        String.format("%.1f", ((double)timeMs / 1000.0)) + ", " +
        String.format("%.0f", ((double)successCount / ((double)timeMs/1000.0))) + ", " +
        String.format("%.2f", ((double)successCount / ((double)timeMs/1000.0)) * messageLength /
                              1048576.0)
    );
  }

  public static void main(String[] args) throws InterruptedException {

    String bootstrapServer = args[0];
    int durationSeconds = Integer.parseInt(args[1]);
    int partitionCount = Integer.parseInt(args[2]);
    int messageLength = Integer.parseInt(args[3]);
    String numAcks = args[4];
    String compression = args[5]; // unused.
    String security = args[6]; // unused.
    String action = args[7];
    int linger = Integer.parseInt(args[8]);

    System.out.println(
        "# Client, [P|C], Broker Version, Partitions, Msg Size, Msg Count, Acks, Compression, TLS, s, Msg/s, Mb/s"
    );

    if (action.equals("Both") || action.equals("Produce"))
    {
      Produce(
        bootstrapServer,
        messageLength,
        durationSeconds,
        numAcks,
        partitionCount,
        linger
      );
    }

    if (action.equals("Both") || action.equals("Consume"))
    {
      Consume(
          bootstrapServer,
          durationSeconds,
          messageLength,
          partitionCount
      );
    }
  }
}
