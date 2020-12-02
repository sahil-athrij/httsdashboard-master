#sudo pkill -f HTTS
sudo pkill -f RabbitMQ_HTTS_Event_Handler
sudo pkill -f Redis_App_HTTS
sleep 2
docker exec python3.8-apps python -u /app/RabbitMQ_HTTS_Event_Handler.py >> ../logs/HTTS_App.log 2>&1 &
sleep 2
docker exec python3.8-apps python -u /app/Redis_App_HTTS.py >> ../logs/HTTS_App.log 2>&1 &
