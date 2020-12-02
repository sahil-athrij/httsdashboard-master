mkdir -p $HOME/HTTSDashboard/RedisDB
docker pull redis:6.0
docker rm -f redis-db
docker run --name redis-db -v $HOME/HTTSDashboard/RedisDB:/data -p 6379:6379 -d redis:6.0 redis-server --appendonly yes
