#!/bin/sh

host="database"
port="5432"

echo "Waiting for database..."

while true; do
    status=$(curl -s http://"$host":"$port"; echo $?)
    [ "$status" == 52 ] && break || sleep 0.1
done

echo "Database is up"

echo "Apply database migrations"
python manage.py migrate

exec "$@"

