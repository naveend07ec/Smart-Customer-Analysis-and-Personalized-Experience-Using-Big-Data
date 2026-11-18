#!/usr/bin/env bash
set -e
export JAVA_HOME=/opt/java/jdk8
export HADOOP_HOME=/opt/hadoop/hadoop-3.3.6
export PATH=$HADOOP_HOME/bin:$PATH

DATA_DIR="/mnt/d/Infynux/big data project/data/raw"

echo "=== Uploading Transactions ==="
$HADOOP_HOME/bin/hdfs dfs -put -f "$DATA_DIR/transactions.csv" hdfs://localhost:9000/customer-analytics/raw/transactions/transactions.csv

echo "=== Uploading Web Activity ==="
$HADOOP_HOME/bin/hdfs dfs -put -f "$DATA_DIR/web_activity.csv" hdfs://localhost:9000/customer-analytics/raw/web_activity/web_activity.csv

echo "=== Uploading Social Media ==="
$HADOOP_HOME/bin/hdfs dfs -put -f "$DATA_DIR/social_media.csv" hdfs://localhost:9000/customer-analytics/raw/social_media/social_media.csv

echo "=== Listing HDFS Raw Storage ==="
$HADOOP_HOME/bin/hdfs dfs -ls -R /customer-analytics/raw

