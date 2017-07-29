#!/bin/bash

if [ "$#" -ne 0 ]; then
    echo "usage: $0"
    exit 1
fi

create_machine()
{
    docker-machine create \
        --engine-install-url=https://web.archive.org/web/20170623081500/https://get.docker.com \
        --amazonec2-region us-west-2 \
        --amazonec2-security-group mhowlett-kafka \
        --driver amazonec2 \
        mhowlett-$1
}

create_machine 1
create_machine 2
create_machine 3
create_machine 4
