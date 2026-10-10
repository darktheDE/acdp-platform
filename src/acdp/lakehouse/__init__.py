"""Lakehouse module for ACDP Platform (Medallion Architecture).

Contains storage engines, schemas, and maintenance utilities for:
- Bronze: Raw immutable web payloads and crawler crawl metadata (Delta Lake + Zstandard).
- Silver: Cleaned, validated, and normalized event models.
- Gold: Dimensional analytical marts.
"""

from acdp.lakehouse.schema import BronzeRecord
from acdp.lakehouse.bronze import (
    compress_payload,
    decompress_payload,
    write_bronze_batch,
    optimize_bronze_table,
    query_bronze_with_duckdb,
)

__all__ = [
    "BronzeRecord",
    "compress_payload",
    "decompress_payload",
    "write_bronze_batch",
    "optimize_bronze_table",
    "query_bronze_with_duckdb",
]
