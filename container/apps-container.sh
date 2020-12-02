cd ./apps
docker build -t python3.8-apps .
docker rm -f python3.8-apps

#Production VM
mkdir -p $HOME/HTTSDashboard/Apps
docker run -itd -v $HOME/HTTSDashboard/Apps:/app -v $HOME/HTTSDashboard/logs:/home/jovyan/logs/ -w /app --name python3.8-apps python3.8-apps bash
