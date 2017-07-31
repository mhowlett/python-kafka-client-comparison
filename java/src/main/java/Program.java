import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.Callback;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;

import java.util.Arrays;
import java.util.Properties;
import java.util.concurrent.TimeUnit;

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
      int messageCount,
      String acks,
      int partitionCount,
      int linger
  ) {
    BasicConfigurator.configure();
    Logger.getRootLogger().setLevel(Level.ERROR);

    Properties props = new Properties();
    props.put("bootstrap.servers", bootstrapServer);
    props.put("acks", acks);
    props.put("retries", 0);
    props.put("linger.ms", linger);
    props.put("key.serializer", "org.apache.kafka.common.serialization.ByteArraySerializer");
    props.put("value.serializer", "org.apache.kafka.common.serialization.ByteArraySerializer");

    byte[] message = new byte[messageLength];
    for (int i=0; i<messageLength; ++i) {
      message[i] = (byte)(48 + i % 10);
    }

    String topicName = "test-topic-p" + partitionCount + "-r3" + "-s" + messageLength;

    Callback cb = new Callback() {
      public void onCompletion(RecordMetadata metadata, Exception e) {
        if (e != null) {
          errorCount += 1;
        }
        else {
          if (successCount == 0) {
            startTime = System.currentTimeMillis();
          }
          successCount += 1;
        }
      }
    };

    Producer<byte[], byte[]> producer = new KafkaProducer<>(props);
    ProducerRecord<byte[], byte[]> record;
    errorCount = 0;
    successCount = 0;
    for (int i = 0; i < messageCount + 1; i++) {
      record = new ProducerRecord<>(topicName, message);
      producer.send(record, cb);
    }

    long waitStartTime = System.currentTimeMillis();

    while (successCount + errorCount < messageCount) {
      try {
        TimeUnit.MILLISECONDS.sleep(20);
      }
      catch (InterruptedException e) {}
    }

    final long endTime = System.currentTimeMillis();

    System.out.println(String.format("# final wait time (ms): {0}", endTime-waitStartTime));

    final long timeMs = (endTime - startTime);
    String version = System.getenv("CONFLUENT");

    System.out.println(
        "P, " +
        "J, " +
        version + ", " +
        partitionCount + ", " +
        messageLength + ", " +
        messageCount + ", " +
        acks + ", " +
        String.format("%.1f", ((double)timeMs / 1000.0)) + ", " +
        String.format("%.0f", ((double)messageCount / ((double)timeMs/1000.0))) + ", " +
        String.format("%.2f", ((double)messageCount / ((double)timeMs/1000.0)) * messageLength /
                               1048576.0)
    );

    producer.close();
  }

  public static void Consume(
      String bootstrapServer,
      int messageCount,
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

    String topicName = "test-topic-p" + partitionCount + "-r3" + "-s" + messageLength;

    int successCount = 0;

    consumer.subscribe(Arrays.asList(topicName));
    while (true) {
      ConsumerRecords<byte[], byte[]> records = consumer.poll(100);
      boolean done = false;
      for (ConsumerRecord<byte[], byte[]> record : records) {
        if (successCount == 0) {
          startTime = System.currentTimeMillis();
        }
        successCount += 1;
        if (successCount > messageCount) {
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
        "C, " +
        "J, " +
        version + ", " +
        partitionCount + ", " +
        messageLength + ", " +
        messageCount + ", " +
        "-, " +
        String.format("%.1f", ((double)timeMs / 1000.0)) + ", " +
        String.format("%.0f", ((double)messageCount / ((double)timeMs/1000.0))) + ", " +
        String.format("%.2f", ((double)messageCount / ((double)timeMs/1000.0)) * messageLength /
                              1048576.0)
    );
  }

  public static void main(String[] args) {

    String bootstrapServer = args[0];
    int messageLength = Integer.parseInt(args[1]);
    int messageCount = Integer.parseInt(args[2]);
    String numAcks = args[3];
    int partitionCount = Integer.parseInt(args[4]);
    int linger = Integer.parseInt(args[5]);

    System.out.println(
        "# Type, Client, Broker, Partitions, Msg Size, Msg Count, Acks, s, Msg/s, Mb/s"
    );

    Produce(
      bootstrapServer,
      messageLength,
      messageCount,
      numAcks,
      partitionCount,
      linger
    );

    Consume(
        bootstrapServer,
        messageCount,
        messageLength,
        partitionCount
    );
  }
}
