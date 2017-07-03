# run the airflow webserver with the "./dags/" directory

afhome=$(pwd)

echo "Setting AIRFLOW_HOME="$afhome

export AIRFLOW_HOME=$afhome

echo "Starting airflow scheduler"

airflow scheduler

