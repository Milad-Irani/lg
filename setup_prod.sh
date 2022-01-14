echo 'script started------'
DOCKER_COM_VERSION=$(which docker-compose ; docker-compose --version)
echo $DOCKER_COM_VERSION

touch info.log
touch error.log
docker-compose up -d --build
echo "worker and server services started"
sleep 5
docker ps
echo "creating a user to login in django admin panel page"
docker exec -it master bash -c "./manage.py createsuperuser --username admin --email admin@deed.com"
