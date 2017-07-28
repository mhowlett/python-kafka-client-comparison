eval $(docker-machine env mhowlett-1)

if [ -z $(docker-machine ssh mhowlett-1 ls / | grep git) ]
  then
  echo "sdf"
fi

#docker-machine ssh mhowlett-1 ls /data

#docker run -it --network=host -v /git/python-client-comparison:/src python:3.6 /src/bootstrap.sh
