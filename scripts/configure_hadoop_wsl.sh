#!/usr/bin/env bash
set -e

HADOOP_CONF_DIR=/opt/hadoop/hadoop-3.3.6/etc/hadoop

echo "=== Configuring hadoop-env.sh ==="
cat << 'EOF' >> "${HADOOP_CONF_DIR}/hadoop-env.sh"

# --- SMART CUSTOMER ANALYTICS HADOOP CONFIGURATION ---
export JAVA_HOME=/opt/java/jdk8
export HADOOP_LOG_DIR=/var/hadoop/logs
export HADOOP_PID_DIR=/var/hadoop/pids

# Strict Memory Limits (256 MB max heap for NameNode and DataNode)
WSL_IP=$(hostname -I | cut -d' ' -f1)
export HADOOP_NAMENODE_OPTS="-Xms128m -Xmx256m -Dhadoop.security.logger=INFO,RFAS -Dhdfs.audit.logger=INFO,NullAppender"
export HADOOP_DATANODE_OPTS="-Xms128m -Xmx256m -Ddfs.datanode.hostname=${WSL_IP} -Dhadoop.security.logger=INFO,RFAS"
EOF

echo "=== Configuring core-site.xml ==="
cat << 'EOF' > "${HADOOP_CONF_DIR}/core-site.xml"
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
        <description>Default HDFS cluster URI</description>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/var/hadoop/tmp</value>
    </property>
    <property>
        <name>io.file.buffer.size</name>
        <value>65536</value>
    </property>
</configuration>
EOF

echo "=== Configuring hdfs-site.xml ==="
WSL_IP=$(hostname -I | cut -d' ' -f1)
cat << EOF > "${HADOOP_CONF_DIR}/hdfs-site.xml"
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///var/hadoop/data/dfs/name</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///var/hadoop/data/dfs/data</value>
    </property>

    <!-- NameNode Binding Addresses -->
    <property>
        <name>dfs.namenode.rpc-address</name>
        <value>0.0.0.0:9000</value>
    </property>
    <property>
        <name>dfs.namenode.rpc-bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.namenode.http-address</name>
        <value>0.0.0.0:9870</value>
    </property>
    <property>
        <name>dfs.namenode.http-bind-host</name>
        <value>0.0.0.0</value>
    </property>

    <!-- DataNode Binding Addresses & Advertising -->
    <property>
        <name>dfs.datanode.address</name>
        <value>${WSL_IP}:9866</value>
    </property>
    <property>
        <name>dfs.datanode.bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.datanode.ipc.address</name>
        <value>${WSL_IP}:9867</value>
    </property>
    <property>
        <name>dfs.datanode.ipc.bind-host</name>
        <value>0.0.0.0</value>
    </property>
    <property>
        <name>dfs.datanode.http.address</name>
        <value>${WSL_IP}:9864</value>
    </property>
    <property>
        <name>dfs.datanode.http.bind-host</name>
        <value>0.0.0.0</value>
    </property>

    <!-- Explicit DataNode Advertised Hostname (dynamically bound to WSL eth0 IP) -->
    <property>
        <name>dfs.datanode.hostname</name>
        <value>${WSL_IP}</value>
    </property>

    <!-- Client DataNode Resolution (ensures clients connect to advertised DataNode IP:9866) -->
    <property>
        <name>dfs.client.use.datanode.hostname</name>
        <value>true</value>
    </property>
    <property>
        <name>dfs.datanode.use.datanode.hostname</name>
        <value>true</value>
    </property>

    <property>
        <name>dfs.permissions.enabled</name>
        <value>false</value>
    </property>
</configuration>
EOF

mkdir -p /var/hadoop/tmp /var/hadoop/pids /var/hadoop/logs
mkdir -p /var/hadoop/data/dfs/name /var/hadoop/data/dfs/data
chown -R naveen:naveen /var/hadoop /opt/hadoop
chmod -R 755 /var/hadoop

echo "Hadoop configuration files written successfully."
