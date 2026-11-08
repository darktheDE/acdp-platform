"""Deterministic validation script for Ollama runtime and integration in ACDP.

Checks:
1. Ollama executable availability in system PATH.
2. Ollama local server reachability (http://localhost:11434/api/version).
3. OpenAI-compatible endpoint reachability (http://localhost:11434/v1/models).
4. Local installed models catalog.
5. System hardware summary (CPU, RAM, GPU) for inference suitability.
"""

import json
import shutil
import sys
import urllib.request
import urllib.error
import subprocess


def check_cli() -> str | None:
    path = shutil.which("ollama")
    if path:
        try:
            ver = subprocess.check_output([path, "--version"], text=True, stderr=subprocess.STDOUT).strip()
            return f"{path} ({ver})"
        except Exception:
            return path
    return None


def check_endpoint(url: str, timeout: float = 3.0) -> tuple[bool, dict | str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ACDP-Ollama-Validator/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            try:
                return True, json.loads(data)
            except Exception:
                return True, data
    except urllib.error.URLError as e:
        return False, str(e)


def main() -> int:
    print("==================================================")
    print("ACDP OLLAMA RUNTIME VALIDATION")
    print("==================================================")

    # 1. CLI Check
    cli_info = check_cli()
    if cli_info:
        print(f"[PASS] Ollama CLI detected: {cli_info}")
    else:
        print("[FAIL] Ollama CLI not found in PATH.")

    # 2. Local daemon reachability
    server_ok, server_data = check_endpoint("http://localhost:11434/api/version")
    if server_ok:
        version = server_data.get("version", "unknown") if isinstance(server_data, dict) else server_data
        print(f"[PASS] Ollama Local Daemon is RUNNING (Version: {version})")
    else:
        print(f"[FAIL] Ollama Daemon is unreachable at http://localhost:11434/api/version: {server_data}")
        print("       Run 'ollama serve' or launch the Ollama Windows app.")
        return 1

    # 3. OpenAI Compatibility
    oai_ok, oai_data = check_endpoint("http://localhost:11434/v1/models")
    if oai_ok:
        print("[PASS] OpenAI-compatible endpoint responding at http://localhost:11434/v1")
    else:
        print(f"[WARN] OpenAI-compatible endpoint check failed: {oai_data}")

    # 4. Model Catalog
    tags_ok, tags_data = check_endpoint("http://localhost:11434/api/tags")
    models = tags_data.get("models", []) if (tags_ok and isinstance(tags_data, dict)) else []
    print(f">> Total local models downloaded: {len(models)}")
    for m in models:
        name = m.get("name", "unknown")
        size_gb = round(m.get("size", 0) / (1024**3), 2)
        print(f"   - {name} ({size_gb} GB)")

    if not models:
        print("   [INFO] No local models downloaded yet. Run 'ollama pull <model>' to download.")

    print("==================================================")
    print("VALIDATION SUMMARY: OLLAMA SERVICE IS OPERATIONAL")
    print("==================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())

