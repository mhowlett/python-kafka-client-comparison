using System;
using System.Text;
using System.Collections.Generic;
using Confluent.Kafka.Serialization;
using Confluent.Kafka;

namespace dotnet
{
    class Program
    {
        static void Main(string[] args)
        {
            var config = new Dictionary<string, object> 
            { 
                { "bootstrap.servers", "54.190.62.218:29093" },
                { "security.protocol", "SSL" },
                { "ssl.ca.location", "/tmp/ca-root.crt" },
                { "debug", "security" }
            };

            string topicName = "test-topic-p1-r3-s64";

            using (var producer = new Producer<Null, string>(config, null, new StringSerializer(Encoding.UTF8)))
            {
                Console.WriteLine($"{producer.Name} producing on {topicName}. q to exit.");

                producer.OnError += (_, error)
                    => Console.WriteLine($"Error: {error}");

                string text;
                while ((text = Console.ReadLine()) != "q")
                {
                    var deliveryReport = producer.ProduceAsync(topicName, null, text);
                    deliveryReport.ContinueWith(task =>
                    {
                        Console.WriteLine($"Partition: {task.Result.Partition}, Offset: {task.Result.Offset}");
                    });
                }

                producer.Flush(10000);
            }
        }
    }
}
