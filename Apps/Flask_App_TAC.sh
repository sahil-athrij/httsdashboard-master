sudo pkill -f Flask_TAC
sleep 2
#docker exec python3.8-flask python -u /app/flask/Flask_App.py >> ../logs/Flask.log 2>&1 &
#docker exec -it python3.8-flask python -u /app/flask/Flask_App.py 
#docker exec -i python3.8-flask python -u /HTTSDashboard/Apps/flask_aci/Flask_ACI.py >> ../logs/Flask_ACI.log 2>&1 &
docker exec -i python3.8-flask python -u /HTTSDashboard/Apps/flask_tac/Flask_TAC.py >> ../logs/TAC/Flask_ACI.log 2>&1 &
