#!/bin/bash
USER='admin'
PASS='cisco!123'
mkdir -p $HOME/HTTSDashboard/data/MongoDB
docker rm -f mongo-db
#sudo rm -rf $HOME/HTTSDashboard/data/MongoDB
docker pull mongo:4.2
docker run --name mongo-db \
	   -v $HOME/HTTSDashboard/data/MongoDB:/data/db \
	   -p 27017:27017 \
	   -e MONGO_INITDB_ROOT_USERNAME="$USER" \
	   -e MONGO_INITDB_ROOT_PASSWORD="$PASS"  \
	   -d mongo:4.2

docker rm -f mongo-express
docker pull mongo-express:0.54
docker run -d \
    --name mongo-express \
    -p 8081:8081 \
    -e ME_CONFIG_MONGODB_SERVER='10.67.82.105' \
    -e ME_CONFIG_BASICAUTH_USERNAME="$USER" \
    -e ME_CONFIG_BASICAUTH_PASSWORD="$PASS" \
    -e ME_CONFIG_MONGODB_ADMINUSERNAME="$USER" \
    -e ME_CONFIG_MONGODB_ADMINPASSWORD="$PASS" \
    -e ME_CONFIG_MONGODB_ENABLE_ADMIN='true' \
    mongo-express:0.54

