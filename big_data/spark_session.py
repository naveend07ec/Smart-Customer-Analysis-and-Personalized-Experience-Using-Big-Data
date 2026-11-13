"""
Spark Session Provider for Big Data Processing Pipeline
Configured for local[2] execution on Windows with 8 GB RAM systems.
"""

import os
import sys
import ctypes
from ctypes import wintypes
from pyspark.sql import SparkSession


def _get_short_path(long_path: str) -> str:
    """Returns 8.3 short path on Windows to avoid path spaces breaking subshells."""
    if os.name != 'nt':
        return long_path
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD

    buf = ctypes.create_unicode_buffer(260)
    res = _GetShortPathNameW(long_path, buf, 260)
    if res > 0 and buf.value:
        return buf.value
    return long_path


def get_spark_session(app_name: str = "SmartCustomerBigDataPipeline") -> SparkSession:
    """
    Initializes and returns a lightweight, controlled PySpark SparkSession.
    Configured specifically for local batch execution on systems with 8 GB RAM.
    """
    # Configure Java runtime if not globally exported
    if "JAVA_HOME" not in os.environ or not os.path.exists(os.environ["JAVA_HOME"]):
        default_jre = r"C:\Program Files\Java\jre1.8.0_471"
        if os.path.exists(default_jre):
            os.environ["JAVA_HOME"] = default_jre

    # Use 8.3 short path for python interpreter on Windows to handle paths with spaces
    short_python = _get_short_path(sys.executable)
    os.environ["PYSPARK_PYTHON"] = short_python
    os.environ["PYSPARK_DRIVER_PYTHON"] = short_python

    # Build memory-conservative SparkSession
    builder = (
        SparkSession.builder
        .master("local[2]")
        .appName(app_name)
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "1g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.default.parallelism", "2")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark
