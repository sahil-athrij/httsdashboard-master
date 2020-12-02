#!/bin/bash
cd ./flask
docker build -t python3.8-flask .

mkdir -p $HOME/HTTSDashboard/Apps
docker rm -f python3.8-flask
#expose both 443 and 8443 port flask
docker run -itd -p 8443:8443 -p 443:443 -v $HOME/HTTSDashboard/:/HTTSDashboard -w /HTTSDashboard/Apps --name python3.8-flask python3.8-flask bash
