#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 <machine-prefix>"
    exit 1
fi

prefix=$1

# AWS specs: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-ec2-config.html

create_machine()
{
    docker-machine create \
        --engine-install-url=https://web.archive.org/web/20170623081500/https://get.docker.com \
        --amazonec2-region us-west-2 \
        --amazonec2-security-group ${prefix}-kafka \
        --amazonec2-instance-type d2.4xlarge \
        --driver amazonec2 \
        ${prefix}-$1
}

create_machine 1
create_machine 2
create_machine 3
create_machine 4
