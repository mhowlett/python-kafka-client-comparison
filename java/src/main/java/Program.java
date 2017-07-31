import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;

import java.util.Arrays;
import java.util.Properties;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;


public class Program {

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
    
    final long startTime = System.currentTimeMillis();
    Producer<Object, String> producer = new KafkaProducer<>(props);
    for (int i = 0; i < messageCount; i++) {
      producer.send(new ProducerRecord<>("my-topic", null, message));
    }
    final long endTime = System.currentTimeMillis();

    System.out.println("Total execution time: " + (endTime - startTime) );

    producer.close();
  }

  public static void Consume(int count) {
    Properties props = new Properties();
    props.put("bootstrap.servers", "localhost:9092");
    props.put("group.id", "test");
    props.put("enable.auto.commit", "true");
    props.put("auto.commit.interval.ms", "1000");
    props.put("session.timeout.ms", "30000");
    props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
    props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
    KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
    consumer.subscribe(Arrays.asList("my-topic"));
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
    int partitionCount = Integer.parseInt(args[3]);

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
