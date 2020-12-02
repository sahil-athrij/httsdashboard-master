docker pull jupyter/base-notebook:latest
docker rm -f jupyter-notebook

cd
cd ~/
docker rm -f jupyter-notebook
docker run --name jupyter-notebook -itd --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v "$PWD":/home/jovyan/ jupyter/base-notebook:latest
sleep 5
docker exec jupyter-notebook jupyter notebook list

