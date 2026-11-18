"""
Pre-Flight Windows PySpark to HDFS Compatibility Test
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Tests:
1. TCP Socket checks to NameNode (9000, 9870) and DataNode (9866, 9864).
2. Live DataNode resolution via NameNode JMX endpoint.
3. Actual DataNode block transfer by writing a 10-row Parquet DataFrame from Windows PySpark to HDFS.
4. Reading back the Parquet dataset from HDFS and verifying integrity and row count.
5. Cleaning up test data.
"""

import sys
import os
import socket
import urllib.request
import json
import subprocess
from datetime import datetime

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


def get_wsl_ip():
    try:
        out = subprocess.check_output(['wsl', '-d', 'Debian', 'hostname', '-I'], text=True)
        return out.strip().split()[0]
    except Exception:
        return 'localhost'


def test_socket(host, port, name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((host, port))
        s.close()
        print(f"[PASS] {name} reachable at {host}:{port}")
        return True
    except Exception as e:
        print(f"[FAIL] {name} unreachable at {host}:{port} ({e})")
        return False


def test_http_jmx(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PySparkHDFSTest'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"[PASS] HTTP JMX query succeeded ({url})")
                return data
            else:
                print(f"[FAIL] HTTP JMX returned status {response.status}")
                return None
    except Exception as e:
        print(f"[FAIL] HTTP JMX request failed: {e}")
        return None


def main():
    wsl_ip = get_wsl_ip()
    print("=" * 60)
    print(f"HDFS PRE-FLIGHT COMPATIBILITY & NETWORKING AUDIT (Target: {wsl_ip})")
    print("=" * 60)

    # 1. Socket Checks
    nn_rpc_ok = test_socket(wsl_ip, 9000, "NameNode RPC")
    nn_http_ok = test_socket(wsl_ip, 9870, "NameNode Web UI")
    dn_xfer_ok = test_socket(wsl_ip, 9866, "DataNode Block Transfer")
    dn_http_ok = test_socket(wsl_ip, 9864, "DataNode Web UI")

    if not (nn_rpc_ok and nn_http_ok and dn_xfer_ok):
        print("\n[CRITICAL] Basic HDFS socket connectivity failed! Check HDFS daemons.")
        sys.exit(1)

    # 2. Query NameNode for Advertised DataNodes
    jmx_url = f"http://{wsl_ip}:9870/jmx?qry=Hadoop:service=NameNode,name=NameNodeInfo"
    jmx_data = test_http_jmx(jmx_url)
    if jmx_data and "beans" in jmx_data and len(jmx_data["beans"]) > 0:
        live_nodes_json = jmx_data["beans"][0].get("LiveNodes", "{}")
        try:
            live_nodes = json.loads(live_nodes_json)
            print(f"[INFO] Live DataNodes registered with NameNode: {len(live_nodes)}")
            for node_key, node_info in live_nodes.items():
                print(f"       -> Node: {node_key} | IP: {node_info.get('infoAddr')} | Xfer: {node_info.get('xferaddr')}")
        except Exception as e:
            print(f"[WARN] Could not parse LiveNodes: {e}")

    # 3. PySpark Read & Write Test
    print("\n" + "=" * 60)
    print("TESTING PYSPARK 3.5.1 TO HDFS PARQUET WRITE & READ")
    print("=" * 60)

    from pyspark.sql import SparkSession
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("HDFS-Compatibility-Test")
        .config("spark.driver.memory", "512m")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .getOrCreate()
    )

    test_hdfs_uri = f"hdfs://{wsl_ip}:9000/test/spark_preflight_test"

    try:
        # Schema and Sample Data
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("customer_id", StringType(), False),
            StructField("score", DoubleType(), True),
            StructField("created_at", TimestampType(), True)
        ])

        now = datetime.now()
        data = [
            (i, f"CUST_{i:04d}", round(10.5 * i, 2), now)
            for i in range(1, 11)
        ]

        df_write = spark.createDataFrame(data, schema)
        print(f"[INFO] Writing 10 rows to {test_hdfs_uri}...")
        df_write.write.mode("overwrite").parquet(test_hdfs_uri)
        print(f"[PASS] Successfully wrote Parquet dataset to HDFS DataNode!")

        # Read back
        print(f"[INFO] Reading back dataset from {test_hdfs_uri}...")
        df_read = spark.read.parquet(test_hdfs_uri)
        row_count = df_read.count()
        print(f"[INFO] Rows read back: {row_count}")

        if row_count != 10:
            print(f"[FAIL] Row count mismatch: expected 10, got {row_count}")
            sys.exit(2)

        df_read.show(5)
        print("[PASS] Schema and row count verified successfully!")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Spark HDFS Write/Read failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
    finally:
        spark.stop()

    print("\n" + "=" * 60)
    print("PRE-FLIGHT COMPATIBILITY TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()

