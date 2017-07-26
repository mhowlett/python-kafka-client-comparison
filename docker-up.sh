#!/bin/bash

docker run -it --network=host -v /git/python-client-comparison:/src python:3.6 /src/bootstrap.sh
