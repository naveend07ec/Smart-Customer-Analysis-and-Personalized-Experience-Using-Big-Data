#!/usr/bin/env bash
export JAVA_HOME=/opt/java/jdk8
export HADOOP_HOME=/opt/hadoop/hadoop-3.3.6
export HADOOP_CONF_DIR=/opt/hadoop/hadoop-3.3.6/etc/hadoop
export PATH=/opt/hadoop/hadoop-3.3.6/bin:/opt/hadoop/hadoop-3.3.6/sbin:/opt/java/jdk8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon stop namenode || true
/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon stop datanode || true
sleep 1

/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon start namenode
/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon start datanode

echo "=== HDFS Started. Monitoring daemons ==="
/opt/java/jdk8/bin/jps -lm

while true; do
    sleep 30
done

