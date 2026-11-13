"""
Spark Session Initializer & Configuration
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Configured for lightweight execution on local developer machines (optimized for <= 8 GB RAM)
with automated Windows environment compatibility.
"""

import os
import sys
import ctypes
from ctypes import wintypes
from pyspark.sql import SparkSession


def get_short_path_name(long_path: str) -> str:
    """Returns the Windows 8.3 short path to safely handle paths with spaces."""
    if os.name != "nt":
        return long_path
    try:
        _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        _GetShortPathNameW.restype = wintypes.DWORD
        buffer_size = 260
        buffer = ctypes.create_unicode_buffer(buffer_size)
        _GetShortPathNameW(long_path, buffer, buffer_size)
        return buffer.value if buffer.value else long_path
    except Exception:
        return long_path


def configure_environment():
    """Sets local runtime environment variables without modifying global system state."""
    # Java runtime setup
    if "JAVA_HOME" not in os.environ:
        default_java = r"C:\Program Files\Java\jre1.8.0_471"
        if os.path.exists(default_java):
            os.environ["JAVA_HOME"] = default_java

    # Project-local Hadoop / winutils setup for Windows
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_hadoop = os.path.join(base_dir, "tools", "hadoop")
    if os.path.exists(local_hadoop) and "HADOOP_HOME" not in os.environ:
        os.environ["HADOOP_HOME"] = local_hadoop
        hadoop_bin = os.path.join(local_hadoop, "bin")
        if hadoop_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = hadoop_bin + os.pathsep + os.environ.get("PATH", "")

    # Python executable for PySpark worker processes
    short_python = get_short_path_name(sys.executable)
    os.environ["PYSPARK_PYTHON"] = short_python
    os.environ["PYSPARK_DRIVER_PYTHON"] = short_python


def get_spark_session(app_name: str = "CustomerBigDataPipeline") -> SparkSession:
    """
    Builds a lightweight local SparkSession restricted to 2 CPU cores and 2 GB RAM.
    """
    configure_environment()

    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName(app_name)
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "1g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.default.parallelism", "2")
        .config("spark.ui.enabled", "false")  # Disables background web UI to conserve RAM
        .config("spark.sql.warehouse.dir", os.path.abspath("spark-warehouse"))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark
