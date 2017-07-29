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

  public static void Produce(int count) {
    BasicConfigurator.configure();
    Logger.getRootLogger().setLevel(Level.DEBUG);

    Properties props = new Properties();
    props.put("bootstrap.servers", "localhost:9092");
    props.put("", "localhost:2181");
    props.put("acks", "all");
    props.put("retries", 0);
    props.put("batch.size", 16384);
    props.put("linger.ms", 1);

    // The total bytes of memory the producer can use to buffer records waiting to be sent to the server.
    // If records are sent faster than they can be delivered to the server the producer will either block
    // or throw an exception based on the preference specified by block.on.buffer.full.
    //               default: 33554432
    props.put("buffer.memory", 1048576);
    props.put("block.on.buffer.full", true);

    // The maximum size of a request. This is also effectively a cap on the maximum record size. Note that
    // the server has its own cap on record size which may be different from this. This setting will limit
    // the number of record batches the producer will send in a single request to avoid sending huge requests.
    //                   default: 1048576
    props.put("max.request.size", 1048576);

    // does it make sense to put the above two equal?

    props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
    props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

    Producer<String, String> producer = new KafkaProducer<>(props);
    for(int i = 0; i < count; i++) {
      producer.send(new ProducerRecord<>("my-topic", Integer.toString(i), Integer.toString(i)));
    }

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
    if (args.length != 2) {
      System.out.println("args: C|P N");
      return;
    }

    int count = Integer.parseInt(args[1]);
    if (args[0].equals("C")) {
      Consume(count);
    }
    else {
      Produce(count);
    }

    System.out.println("done...");
  }
}
