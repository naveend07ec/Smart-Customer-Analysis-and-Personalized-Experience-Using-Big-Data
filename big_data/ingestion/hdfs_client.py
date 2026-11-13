"""
Apache Hadoop HDFS Integration & Verification Module
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Provides:
1. Genuine HDFS cluster connectivity checks (WebHDFS / NameNode RPC).
2. Dataset staging and upload utilities (local -> HDFS).
3. Graceful dual-mode operation:
   - Mode A: Genuine Apache Hadoop HDFS (hdfs://localhost:9000 or WebHDFS)
   - Mode B: Local filesystem staged storage (zero-daemon fallback for 8 GB RAM machines)
"""

import os
import subprocess
import urllib.request
import json
from typing import Dict, Any, Optional


class HDFSManager:
    def __init__(self, namenode_url: str = "http://localhost:9870", rpc_host: str = "hdfs://localhost:9000"):
        self.namenode_url = namenode_url
        self.rpc_host = rpc_host
        self.base_hdfs_path = "/user/hadoop/customer_analytics"

    def check_hdfs_status(self) -> Dict[str, Any]:
        """
        Pings WebHDFS NameNode HTTP endpoint (default port 9870 for Hadoop 3.x).
        """
        webhdfs_url = f"{self.namenode_url}/jmx?qry=Hadoop:service=NameNode,name=NameNodeInfo"
        try:
            req = urllib.request.Request(webhdfs_url, headers={"User-Agent": "HDFS-Client"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    beans = data.get("beans", [{}])[0]
                    return {
                        "is_available": True,
                        "cluster_status": "ONLINE",
                        "namenode_url": self.namenode_url,
                        "rpc_endpoint": self.rpc_host,
                        "total_capacity_gb": round(beans.get("Total", 0) / (1024**3), 2),
                        "used_capacity_gb": round(beans.get("Used", 0) / (1024**3), 2),
                        "live_datanodes": beans.get("NumLiveDataNodes", 0),
                        "mode": "GENUINE_HDFS"
                    }
        except Exception as e:
            return {
                "is_available": False,
                "cluster_status": "OFFLINE",
                "message": f"Hadoop NameNode not reachable at {self.namenode_url} ({e})",
                "mode": "LOCAL_STAGED_STORE_FALLBACK",
                "active_storage_path": os.path.abspath("data/processed")
            }

    def upload_to_hdfs(self, local_path: str, hdfs_target_path: Optional[str] = None) -> bool:
        """
        Uploads a local file/directory to HDFS using 'hdfs dfs -put' if Hadoop CLI is present.
        """
        if not os.path.exists(local_path):
            print(f"Error: Local path '{local_path}' does not exist.")
            return False

        target = hdfs_target_path or f"{self.base_hdfs_path}/raw/{os.path.basename(local_path)}"
        cmd = ["hdfs", "dfs", "-put", "-f", local_path, target]

        try:
            print(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Successfully uploaded {local_path} to HDFS {target}")
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Hadoop CLI not available or upload failed: {e}")
            return False


def main():
    print("=" * 70)
    print("HADOOP HDFS CONNECTIVITY & CLUSTER DIAGNOSTIC")
    print("=" * 70)

    manager = HDFSManager()
    status = manager.check_hdfs_status()

    if status["is_available"]:
        print(f"Status: Genuine Hadoop HDFS cluster is ONLINE!")
        print(f"  NameNode: {status['namenode_url']}")
        print(f"  RPC Host: {status['rpc_endpoint']}")
        print(f"  Live DataNodes: {status['live_datanodes']}")
        print(f"  Capacity: {status['used_capacity_gb']} GB used / {status['total_capacity_gb']} GB total")
    else:
        print(f"Status: Genuine Hadoop NameNode is currently OFFLINE ({status['mode']}).")
        print(f"  Detail: {status['message']}")
        print(f"  Active Storage Fallback: {status['active_storage_path']}")
        print("\nAcademic Note:")
        print("  - For lightweight 8 GB RAM machines, the project runs seamlessly using local staged Parquet storage.")
        print("  - When Hadoop daemons are started, set HADOOP_URI=hdfs://localhost:9000 to enable native distributed cluster storage.")

    print("=" * 70)


if __name__ == "__main__":
    main()
