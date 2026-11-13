"""
PyArrow-based Local Export Utility for PySpark DataFrames
Provides memory-conscious, verified exports on Windows without winutils.exe.
"""

import os
import shutil
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pacsv
from pyspark.sql import DataFrame


def _safe_remove(target_path: str):
    """Safely removes an existing file or directory to prevent permission collisions."""
    if os.path.exists(target_path):
        if os.path.isdir(target_path):
            shutil.rmtree(target_path)
        else:
            os.remove(target_path)


def export_spark_dataframe(
    df: DataFrame,
    output_dir: str,
    base_name: str,
    batch_size: int = 25000,
    export_parquet: bool = True,
    export_csv: bool = True
) -> dict:
    """
    Exports a PySpark DataFrame to local Parquet and/or CSV files using PyArrow.
    Uses batch streaming to prevent memory spikes on 8 GB RAM machines.
    Verifies that exported files exist and can be read back with exact row counts.
    """
    os.makedirs(output_dir, exist_ok=True)
    parquet_path = os.path.join(output_dir, f"{base_name}.parquet")
    csv_path = os.path.join(output_dir, f"{base_name}.csv")

    # Safely clear any pre-existing file or directory with target names
    if export_parquet:
        _safe_remove(parquet_path)
    if export_csv:
        _safe_remove(csv_path)

    spark_total_rows = df.count()
    field_names = df.columns

    # Fetch rows using local iterator in batches for constant memory usage
    row_iter = df.toLocalIterator()

    parquet_writer = None
    all_batches = []
    current_batch = []

    try:
        for row in row_iter:
            current_batch.append(row.asDict())
            if len(current_batch) >= batch_size:
                batch_table = pa.Table.from_pylist(current_batch)
                if export_parquet:
                    if parquet_writer is None:
                        parquet_writer = pq.ParquetWriter(parquet_path, batch_table.schema)
                    parquet_writer.write_table(batch_table)
                all_batches.append(batch_table)
                current_batch = []

        # Flush any remaining rows
        if current_batch:
            batch_table = pa.Table.from_pylist(current_batch)
            if export_parquet:
                if parquet_writer is None:
                    parquet_writer = pq.ParquetWriter(parquet_path, batch_table.schema)
                parquet_writer.write_table(batch_table)
            all_batches.append(batch_table)

    finally:
        if parquet_writer is not None:
            parquet_writer.close()

    # Consolidate Arrow table for CSV export
    if export_csv:
        if all_batches:
            full_table = pa.concat_tables(all_batches)
        else:
            # Handle empty dataframe edge case
            full_table = pa.Table.from_pylist([], schema=pa.schema([pa.field(c, pa.string()) for c in field_names]))
        pacsv.write_csv(full_table, csv_path)

    # Verification: Read back and assert row counts match Spark
    verification = {
        "base_name": base_name,
        "spark_row_count": spark_total_rows,
        "parquet_verified": False,
        "csv_verified": False,
        "parquet_path": parquet_path if export_parquet else None,
        "csv_path": csv_path if export_csv else None,
        "parquet_row_count": None,
        "csv_row_count": None
    }

    if export_parquet and os.path.exists(parquet_path):
        read_pq = pq.read_table(parquet_path)
        verification["parquet_row_count"] = read_pq.num_rows
        verification["parquet_verified"] = (read_pq.num_rows == spark_total_rows)
        if not verification["parquet_verified"]:
            raise ValueError(f"Parquet row count mismatch for {base_name}: expected {spark_total_rows}, got {read_pq.num_rows}")

    if export_csv and os.path.exists(csv_path):
        read_csv = pacsv.read_csv(csv_path)
        verification["csv_row_count"] = read_csv.num_rows
        verification["csv_verified"] = (read_csv.num_rows == spark_total_rows)
        if not verification["csv_verified"]:
            raise ValueError(f"CSV row count mismatch for {base_name}: expected {spark_total_rows}, got {read_csv.num_rows}")

    return verification
