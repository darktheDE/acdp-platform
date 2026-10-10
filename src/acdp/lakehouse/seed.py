"""Seed Ingestion Script for Bronze Layer.

Ingests sample crawl HTML files from data/raw/html/ into the Bronze Delta Lake table.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

from acdp.config import settings
from acdp.lakehouse.bronze import (
    compress_payload,
    get_delta_table,
    query_bronze_with_duckdb,
    write_bronze_batch,
)
from acdp.lakehouse.schema import BronzeRecord


def run_seed_ingestion() -> None:
    """Read HTML files from data/raw/html/ and write them as Batch #0 into Bronze."""
    raw_html_dir = Path("data/raw/html")
    if not raw_html_dir.exists():
        print(f"Error: Directory {raw_html_dir} does not exist.", file=sys.stderr)
        sys.exit(1)

    html_files = sorted(list(raw_html_dir.glob("*.html")))
    if not html_files:
        print(f"No .html files found in {raw_html_dir}.")
        return

    print(f"Found {len(html_files)} sample HTML files in {raw_html_dir}.")
    records: list[BronzeRecord] = []
    total_uncompressed_bytes = 0
    total_compressed_bytes = 0

    for file_path in html_files:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        domain = file_path.stem.replace(".html", "")
        source_url = f"https://{domain}"

        record = BronzeRecord.create(
            source_url=source_url,
            source_domain=domain,
            raw_html=content,
            compress_fn=compress_payload,
            metadata={"seed_file": file_path.name, "ingested_by": "seed_pipeline"},
            crawled_at=datetime.now(timezone.utc),
        )

        uncompressed_len = len(content.encode("utf-8"))
        compressed_len = len(record.raw_html_bytes)
        total_uncompressed_bytes += uncompressed_len
        total_compressed_bytes += compressed_len

        print(
            f"  - [{domain}]: {uncompressed_len:,} bytes -> {compressed_len:,} bytes "
            f"({(compressed_len / uncompressed_len) * 100:.1f}%)"
        )
        records.append(record)

    # Ingest batch into Delta Lake
    print(f"\nWriting {len(records)} records to Bronze Delta table at: {settings.bronze_storage_uri}")
    written_count = write_bronze_batch(records)
    print(f"Successfully written: {written_count} records.")

    # Inspect Delta Table version
    dt = get_delta_table()
    print(f"Delta Table Version: {dt.version()}")
    print(f"Total Parquet Files: {len(dt.file_uris())}")

    # Compression efficiency summary
    ratio = (total_compressed_bytes / total_uncompressed_bytes) * 100 if total_uncompressed_bytes else 0
    savings = 100 - ratio
    print("\nCompression Efficiency Summary:")
    print(f"  Total Uncompressed: {total_uncompressed_bytes:,} bytes")
    print(f"  Total Compressed:   {total_compressed_bytes:,} bytes")
    print(f"  Space Savings:      {savings:.1f}%")

    # Verification via DuckDB query
    print("\nVerifying data via DuckDB query (delta_scan):")
    try:
        uri = settings.bronze_storage_uri.replace("\\", "/")
        query = f"""
            SELECT 
                raw_id, 
                source_domain, 
                crawled_at, 
                http_status, 
                octet_length(raw_html_bytes) as compressed_bytes
            FROM delta_scan('{uri}')
            ORDER BY crawled_at DESC
        """
        relation = query_bronze_with_duckdb(query)

        arrow_tbl = relation.arrow().read_all()
        for i in range(arrow_tbl.num_rows):
            domain = arrow_tbl.column("source_domain")[i].as_py()
            status = arrow_tbl.column("http_status")[i].as_py()
            size = arrow_tbl.column("compressed_bytes")[i].as_py()
            crawled = arrow_tbl.column("crawled_at")[i].as_py()
            print(f"  * {domain:<35} | Status: {status} | Compressed: {size:>6,} B | Crawled: {crawled}")
    except Exception as e:
        print(f"DuckDB query note/warning: {e}")




if __name__ == "__main__":
    run_seed_ingestion()
