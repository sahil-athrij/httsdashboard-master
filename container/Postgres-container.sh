mkdir -p $HOME/HTTSDashboard/PostgreSQLDB
docker pull postgres:12
docker rm -f postgres-db
docker run -it --name postgres-db -p 5432:5432 -v $HOME/HTTSDashboard/PostgreSQLDB:/var/lib/postgresql/data -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=cisco!123 -d postgres:12
