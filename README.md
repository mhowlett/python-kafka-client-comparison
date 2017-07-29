## Python Kafka Client Performance Tests

use `aws-machines-up.sh` to bring up and provision with docker a 3-broker kafka cluster + (separate) zookeeper server on AWS.

use `aws-machines-down.sh` to bring them down again and terminate them.

use `cluster-up.sh {confluent-version}` to bring up the kafka cluster + create topic `test-topic`.

use `cluster-down.sh` to stop the cluster (and destroy any data).

use `docker-up.sh {confluent-verision}` to start a docker instance (on the zookeeper server). Following env variables set:

  - `KAFKA` - the address:port of a kafka broker to use as bootstrap server.
  - `ZOOKEEPER` - address:port of the zookeeper broker.
  - `CONFLUENT` = `{confluent-version}`.
  