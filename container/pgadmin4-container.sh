mkdir -p $HOME/HTTSDashboard/pgadmin4
docker pull dpage/pgadmin4
docker rm -f pgadmin4
docker run --name pgadmin4 -v $HOME/HTTSDashboard/pgadmin4:/var/lib/pgadmin -p 8086:80 -e "PGADMIN_DEFAULT_EMAIL=admin@htts.syd" -e "PGADMIN_DEFAULT_PASSWORD=cisco!123" -d dpage/pgadmin4
