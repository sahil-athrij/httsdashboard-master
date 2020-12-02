docker pull rabbitmq:3.8-management
docker rm -f rabbitmq-broker
docker run -d --hostname my-rabbit --name rabbitmq-broker -p 5672:5672 -p 15671:15671 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=admin -e RABBITMQ_DEFAULT_PASS=cisco!123 rabbitmq:3.8-management
