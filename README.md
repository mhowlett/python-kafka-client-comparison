## Python Kafka Client Performance Tests

use `aws-machines-up.sh` to bring up four AWS d2.xlarge instances and configure them for use with `docker-machine`.

use `aws-machines-down.sh` to bring these down again and terminate them.

use `cluster-up.sh {confluent-version}` to bring up the kafka cluster + create the test topics.

use `cluster-down.sh` to stop the cluster (and destroy any data).

use `python-env-up.sh` to bring up a docker image on node 1 set up for running python tests (all clients)

use `java-env-up.sh` to bring up a docker image on node 1 set up for running java tests.

use `run-tests.sh <confluent-version-number> <client> <message-count> <java|python>` to run a complete set of perf tests.

note: inside test container, the following environment variables are set:
  - `KAFKA` - the address:port of a kafka broker to use as bootstrap server.
  - `ZOOKEEPER` - address:port of the zookeeper broker.
  - `CONFLUENT` = `{confluent-version}`.
  