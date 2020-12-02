sudo pkill -f RabbitMQ_TAC_Event_Handler
sudo pkill -f Redis_App_TAC
sleep 2
docker exec python3.8-apps python -u /app/RabbitMQ_TAC_Event_Handler.py >> ../logs/TAC_App.log 2>&1 &
sleep 2
docker exec python3.8-apps python -u /app/Redis_App_TAC.py >> ../logs/TAC_App.log 2>&1 &
