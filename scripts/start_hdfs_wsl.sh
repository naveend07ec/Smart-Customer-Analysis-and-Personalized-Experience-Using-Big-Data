#!/usr/bin/env bash
export JAVA_HOME=/opt/java/jdk8
export HADOOP_HOME=/opt/hadoop/hadoop-3.3.6
export HADOOP_CONF_DIR=/opt/hadoop/hadoop-3.3.6/etc/hadoop
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$JAVA_HOME/bin:$PATH

echo "=== Stopping any existing daemons ==="
${HADOOP_HOME}/bin/hdfs --daemon stop namenode || true
${HADOOP_HOME}/bin/hdfs --daemon stop datanode || true
killall -9 java 2>/dev/null || true
sleep 1

echo "=== Starting NameNode and DataNode ==="
${HADOOP_HOME}/bin/hdfs --daemon start namenode
sleep 3
${HADOOP_HOME}/bin/hdfs --daemon start datanode
sleep 3

echo "=== Checking Processes ==="
jps -lm

echo "=== Testing HDFS DFSAdmin Report ==="
${HADOOP_HOME}/bin/hdfs dfsadmin -report

