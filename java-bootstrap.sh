#!/bin/bash

apt-get update
apt-get install -y emacs
apt-get install -y less
apt-get install -y maven
apt-get install -y wamerican

cd /src/java
mvn package
bash
