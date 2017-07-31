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

  public static void Produce(String bootstrapServer, int messageLength, int messageCount, String acks, int partitionCount) {
    BasicConfigurator.configure();
    Logger.getRootLogger().setLevel(Level.ERROR);

    Properties props = new Properties();
    props.put("bootstrap.servers", bootstrapServer);
    props.put("acks", acks);
    props.put("retries", 0);
    props.put("batch.size", 16384);
    props.put("linger.ms", 50);
    props.put("block.on.buffer.full", true);
    props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
    props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

    StringBuilder sb = new StringBuilder();
    for (int i=0; i<messageLength; ++i) {
      sb.append((char)(48 + i % 10));
    }
    String message = sb.toString();

    String topicName = "test-topic-p" + partitionCount + "-r3";

    Producer<Object, String> producer = new KafkaProducer<>(props);
    errorCount = 0;
    successCount = 0;
    for (int i = 0; i < messageCount + 1; i++) {
      producer.send(
          new ProducerRecord<>(topicName, null, message),
          new Callback() {
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
              System.out.println("The offset of the record we just sent is: " + metadata.offset());
            }
          });
    }

    while (successCount + errorCount < messageCount) {
      try {
        TimeUnit.MILLISECONDS.sleep(20);
      }
      catch (InterruptedException e) {}
    }

    final long endTime = System.currentTimeMillis();

    System.out.println("Total execution time: " + (endTime - startTime) );

    producer.close();
  }

  public static void Consume(int count, int partitionCount) {
    Properties props = new Properties();
    props.put("bootstrap.servers", "localhost:9092");
    props.put("group.id", "test");
    props.put("enable.auto.commit", "true");
    props.put("auto.commit.interval.ms", "1000");
    props.put("session.timeout.ms", "30000");
    props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
    props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
    KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);

    String topicName = "test-topic-p" + partitionCount + "-r3";

    consumer.subscribe(Arrays.asList(topicName));
    while (true) {
      ConsumerRecords<String, String> records = consumer.poll(100);
      for (ConsumerRecord<String, String> record : records)
        System.out.printf("offset = %d, key = %s, value = %s", record.offset(), record.key(), record.value());
    }
  }

  public static void main(String[] args) {

    String bootstrapServer = args[0];
    int messageLength = Integer.parseInt(args[1]);
    int messageCount = Integer.parseInt(args[2]);
    String numAcks = args[3];
    int partitionCount = Integer.parseInt(args[4]);

    Produce(
      bootstrapServer,
      messageLength,
      messageCount,
      numAcks,
      partitionCount
    );

    // Consume(messageCount);
  }
}
