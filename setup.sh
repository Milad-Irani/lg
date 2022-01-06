echo 'script started------'
DOCKER_COM_VERSION=$(which docker-compose ; docker-compose --version)
echo $DOCKER_COM_VERSION
echo '--------------------'
echo "first thing to do is setup the database."
docker run --rm -p 5432:5432 --name lg_postgres --network lg_default -e POSTGRES_PASSWORD=postgres_pass -e POSTGRES_USER=postgres_user -d postgres

echo "database started----"

touch info.log
touch error.log
docker-compose up -d --build
echo "worker and server services started"
echo "read bellow to ensure there are two services named lg_server and lg_worker works as expected"
echo "to creating tables migrations , we wait 2 seconds"
sleep 2
docker ps
echo "creating a user to login in django admin panel page"
docker exec -it lg_server bash -c "./manage.py createsuperuser --username milad --email milad@test.com"
echo "now your username is milad . login to 127.0.0.1:8000/admin/ and enjoy:)) "
