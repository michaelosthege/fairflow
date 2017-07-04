# run the airflow webserver with the "./dags/" directory

afhome=$(pwd)

echo "Setting AIRFLOW_HOME="$afhome

export AIRFLOW_HOME=$afhome

echo "Initializing airflow db"

service mysql start
airflow resetdb
airflow initdb

