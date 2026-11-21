"""Deterministic OpenAPI 3.1 schema exporter for Spec-Driven TypeScript codegen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from acdp.api.main import app


def export_openapi_schema(output_path: Path) -> Path:
    """Write FastAPI OpenAPI 3.1 JSON schema deterministically without starting a server."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export ACDP FastAPI OpenAPI 3.1 specification")
    parser.add_argument("--output", default="openapi.json", help="Destination path for openapi.json")
    args = parser.parse_args()
    out = export_openapi_schema(Path(args.output))
    print(f"Exported OpenAPI 3.1 schema -> {out}")
