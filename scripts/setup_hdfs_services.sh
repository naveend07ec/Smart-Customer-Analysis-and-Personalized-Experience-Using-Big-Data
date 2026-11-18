#!/usr/bin/env bash
set -e

echo "=== Creating systemd service for NameNode ==="
cat << 'EOF' > /etc/systemd/system/hadoop-namenode.service
[Unit]
Description=Apache Hadoop HDFS NameNode
After=network.target

[Service]
Type=forking
User=naveen
Group=naveen
Environment="JAVA_HOME=/opt/java/jdk8"
Environment="HADOOP_HOME=/opt/hadoop/hadoop-3.3.6"
Environment="HADOOP_CONF_DIR=/opt/hadoop/hadoop-3.3.6/etc/hadoop"
ExecStart=/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon start namenode
ExecStop=/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon stop namenode
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "=== Creating systemd service for DataNode ==="
cat << 'EOF' > /etc/systemd/system/hadoop-datanode.service
[Unit]
Description=Apache Hadoop HDFS DataNode
After=network.target hadoop-namenode.service

[Service]
Type=forking
User=naveen
Group=naveen
Environment="JAVA_HOME=/opt/java/jdk8"
Environment="HADOOP_HOME=/opt/hadoop/hadoop-3.3.6"
Environment="HADOOP_CONF_DIR=/opt/hadoop/hadoop-3.3.6/etc/hadoop"
ExecStart=/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon start datanode
ExecStop=/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon stop datanode
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "Starting hadoop-namenode..."
systemctl start hadoop-namenode
sleep 3
echo "Starting hadoop-datanode..."
systemctl start hadoop-datanode
sleep 3

echo "=== Checking Service Status ==="
systemctl status hadoop-namenode --no-pager
systemctl status hadoop-datanode --no-pager

