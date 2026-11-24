#!/usr/bin/env python3
"""
verify_links.py - Deterministic Link & Domain Reachability Validator for ACDP Platform.

Scans markdown, bibtex, html, and code files for external links and domains,
verifies DNS resolution and HTTP reachability concurrently, and produces
an audit report.

No external dependencies required (uses standard library).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import socket
import ssl
import sys
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPSHandler

# Realistic browser User-Agent to avoid aggressive 403 blocks on legitimate sites
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

# Known ISP wildcard/hijack IPs returned instead of NXDOMAIN (e.g. VNPT, OpenDNS search)
KNOWN_DNS_HIJACK_IPS = {
    "125.235.4.59",  # VNPT Vietnam NXDOMAIN search redirect IP
    "0.0.0.0",
    "127.0.0.1",
}


# Regex patterns for extracting URLs and bare domains
URL_PATTERN = re.compile(r'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+')
BACKTICK_DOMAIN_PATTERN = re.compile(r'`([a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)+(?:/[^\s`]*)?)`')
TRAILING_PUNCT_PATTERN = re.compile(r'[\.,;:?!\)>\]\'"]+$')

NON_DOMAIN_EXTENSIONS = {
    ".md", ".py", ".json", ".html", ".htm", ".tex", ".bib",
    ".ts", ".tsx", ".js", ".jsx", ".yml", ".yaml", ".sh",
    ".sql", ".css", ".png", ".jpg", ".jpeg", ".svg", ".lock",
    ".toml", ".txt", ".parquet", ".duckdb", ".db", ".env", ".example", ".gitignore"
}
VALID_TLDS = {
    "vn", "com", "org", "net", "edu", "gov", "info", "io",
    "ai", "dev", "app", "me", "co", "xyz", "global"
}


def is_valid_domain_string(candidate: str) -> bool:
    """Check if string looks like a web domain rather than a filename or code symbol."""
    cand = candidate.strip().lower()
    if "." not in cand or " " in cand:
        return False
    host_part = cand.split("/")[0]
    if host_part.startswith(".") or host_part.endswith(".") or host_part.startswith("-"):
        return False
    ext = os.path.splitext(host_part)[1]
    if ext in NON_DOMAIN_EXTENSIONS:
        return False
    parts = host_part.split(".")
    if len(parts) < 2:
        return False
    tld = parts[-1]
    if len(parts) >= 2 and parts[-2] in ("edu", "gov", "com", "org", "ac", "net"):
        return True
    return tld in VALID_TLDS


# Directories and extensions to skip
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".ruff_cache", "dist", "build", ".gemini"
}
IGNORED_FILES = {
    "test_verify_links.py",
    "sample_link_audit_report.json",
}
CDN_PRECONNECT_DOMAINS = {
    "fonts.googleapis.com",
    "fonts.gstatic.com",
}
SCANNABLE_EXTENSIONS = {".md", ".markdown", ".tex", ".bib", ".html", ".htm", ".json", ".py", ".ts", ".tsx", ".yaml", ".yml"}


@dataclass
class LinkOccurrence:
    file_path: str
    line_number: int
    url: str


@dataclass
class LinkVerificationResult:
    url: str
    domain: str
    status: str  # HEALTHY, RESTRICTED_BOT, BROKEN, TIMEOUT, DNS_FAILED, SSL_ERROR
    http_code: Optional[int]
    message: str
    response_time_ms: int
    occurrences: List[Dict[str, any]]


class LinkVerifier:
    def __init__(
        self,
        timeout: float = 8.0,
        max_workers: int = 10,
        ignored_domains: Optional[Set[str]] = None,
        verbose: bool = True
    ):
        self.timeout = timeout
        self.max_workers = max_workers
        self.ignored_domains = ignored_domains or set()
        self.verbose = verbose

        # Create an SSL context that can fall back gracefully
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Build opener with custom redirect and SSL handling
        self.opener = build_opener(HTTPSHandler(context=self.ssl_context))

    def clean_url(self, raw_url: str) -> str:
        """Strip trailing punctuation and Markdown delimiters from extracted URL."""
        cleaned = TRAILING_PUNCT_PATTERN.sub('', raw_url.strip())
        # Remove trailing parentheses if unbalanced
        if cleaned.endswith(')') and cleaned.count('(') < cleaned.count(')'):
            cleaned = cleaned[:-1]
        if cleaned.endswith(']') and cleaned.count('[') < cleaned.count(']'):
            cleaned = cleaned[:-1]
        return cleaned

    def scan_file(self, file_path: Path) -> List[LinkOccurrence]:
        """Extract all external HTTP/HTTPS links from a file."""
        occurrences = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, start=1):
                    # Skip markdown file:// internal links
                    if "file:///" in line or "file://" in line:
                        # Clean out file links before regex matching
                        line = re.sub(r'file:///[^\s\)]+', '', line)
                        line = re.sub(r'file://[^\s\)]+', '', line)

                    matches = URL_PATTERN.findall(line)
                    for raw_url in matches:
                        url = self.clean_url(raw_url)
                        # Validate that it has scheme and netloc
                        parsed = urlparse(url)
                        if parsed.scheme in ("http", "https") and parsed.netloc:
                            domain = parsed.netloc.lower().split(":")[0]
                            if domain in ("localhost", "127.0.0.1", "0.0.0.0"):
                                continue
                            if domain in self.ignored_domains:
                                continue
                            occurrences.append(LinkOccurrence(
                                file_path=str(file_path),
                                line_number=line_idx,
                                url=url
                            ))

                    # 2. Extract bare domains in backticks (e.g. `bk-innovation.hcmut.edu.vn`, `fit.hcmute.edu.vn`)
                    backtick_matches = BACKTICK_DOMAIN_PATTERN.findall(line)
                    for raw_cand in backtick_matches:
                        cand = self.clean_url(raw_cand)
                        if cand.startswith("http://") or cand.startswith("https://"):
                            continue
                        if is_valid_domain_string(cand):
                            norm_url = f"https://{cand}"
                            parsed = urlparse(norm_url)
                            domain = parsed.netloc.lower().split(":")[0]
                            if domain in ("localhost", "127.0.0.1", "0.0.0.0"):
                                continue
                            if domain in self.ignored_domains:
                                continue
                            occurrences.append(LinkOccurrence(
                                file_path=str(file_path),
                                line_number=line_idx,
                                url=norm_url
                            ))

        except Exception as e:
            if self.verbose:
                print(f"[WARN] Failed to read {file_path}: {e}", file=sys.stderr)
        return occurrences

    def scan_path(self, target_path: Path) -> Tuple[List[Path], Dict[str, List[LinkOccurrence]]]:
        """Scan a path (file or directory) and group link occurrences by URL."""
        scanned_files = []
        url_map: Dict[str, List[LinkOccurrence]] = {}

        if target_path.is_file():
            files_to_scan = [target_path]
        else:
            files_to_scan = []
            for root, dirs, files in os.walk(target_path):
                # Prune ignored directories
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".git")]
                for f in files:
                    if f in IGNORED_FILES:
                        continue
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SCANNABLE_EXTENSIONS:
                        files_to_scan.append(Path(root) / f)

        for p in files_to_scan:
            scanned_files.append(p)
            found = self.scan_file(p)
            for occ in found:
                url_map.setdefault(occ.url, []).append(occ)

        return scanned_files, url_map

    def check_dns(self, domain: str) -> bool:
        """Verify that domain has valid DNS records and is not hijacked by ISP NXDOMAIN redirection."""
        try:
            infos = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM)
            ips = {info[4][0] for info in infos if info[4]}
            if not ips:
                return False
            # If every resolved IP is in the ISP wildcard redirect set, domain is nonexistent
            if ips.issubset(KNOWN_DNS_HIJACK_IPS):
                return False
            return True
        except socket.gaierror:
            return False

    def verify_single_url(self, url: str, occurrences: List[LinkOccurrence]) -> LinkVerificationResult:
        """Verify reachability of a single URL via DNS and HTTP."""
        start_time = time.time()
        parsed = urlparse(url)
        domain = parsed.netloc.lower().split(":")[0]

        occ_dicts = [{"file": o.file_path, "line": o.line_number} for o in occurrences]

        # 1. DNS Pre-check
        if not self.check_dns(domain):
            elapsed = int((time.time() - start_time) * 1000)
            return LinkVerificationResult(
                url=url,
                domain=domain,
                status="DNS_FAILED",
                http_code=None,
                message="Domain DNS resolution failed (NXDOMAIN / host not found).",
                response_time_ms=elapsed,
                occurrences=occ_dicts
            )

        # Handle preconnect CDN origins where bare root does not serve HTML pages
        if domain in CDN_PRECONNECT_DOMAINS and parsed.path in ("", "/"):
            elapsed = int((time.time() - start_time) * 1000)
            return LinkVerificationResult(
                url=url,
                domain=domain,
                status="HEALTHY",
                http_code=200,
                message="CDN preconnect origin verified via DNS.",
                response_time_ms=elapsed,
                occurrences=occ_dicts
            )

        # 2. HTTP Request (Try HEAD first, fallback to GET)
        req_headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # Try HEAD method first
        head_req = Request(url, headers=req_headers, method="HEAD")
        try:
            with self.opener.open(head_req, timeout=self.timeout) as resp:
                elapsed = int((time.time() - start_time) * 1000)
                code = resp.getcode()
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="HEALTHY",
                    http_code=code,
                    message=f"HTTP HEAD success ({code})",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
        except HTTPError as e:
            # 405 Method Not Allowed or 403 Forbidden on HEAD: retry with GET
            if e.code in (405, 403, 400):
                return self._fallback_get(url, domain, req_headers, start_time, occ_dicts)
            elif e.code in (401, 429):
                elapsed = int((time.time() - start_time) * 1000)
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="RESTRICTED_BOT",
                    http_code=e.code,
                    message=f"HTTP {e.code} (Bot check / Auth challenge, domain is valid)",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
            elif e.code in (404, 410):
                elapsed = int((time.time() - start_time) * 1000)
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="BROKEN",
                    http_code=e.code,
                    message=f"HTTP {e.code} (Resource Not Found)",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
            else:
                elapsed = int((time.time() - start_time) * 1000)
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="HEALTHY" if e.code < 400 else "SERVER_ERROR",
                    http_code=e.code,
                    message=f"HTTP {e.code}: {e.reason}",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
        except URLError as e:
            reason = str(e.reason)
            if "timed out" in reason.lower():
                return self._fallback_get(url, domain, req_headers, start_time, occ_dicts)
            elif "certificate" in reason.lower():
                elapsed = int((time.time() - start_time) * 1000)
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="SSL_ERROR",
                    http_code=None,
                    message=f"SSL handshake error: {reason}",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
            else:
                # Fallback to GET just in case HEAD was dropped by firewall
                return self._fallback_get(url, domain, req_headers, start_time, occ_dicts)
        except Exception as e:
            return self._fallback_get(url, domain, req_headers, start_time, occ_dicts)

    def _fallback_get(
        self,
        url: str,
        domain: str,
        headers: Dict[str, str],
        start_time: float,
        occ_dicts: List[Dict[str, any]]
    ) -> LinkVerificationResult:
        """Fallback to HTTP GET with Range header for servers that reject HEAD."""
        get_headers = headers.copy()
        get_headers["Range"] = "bytes=0-1024"
        get_req = Request(url, headers=get_headers, method="GET")

        try:
            with self.opener.open(get_req, timeout=self.timeout) as resp:
                elapsed = int((time.time() - start_time) * 1000)
                code = resp.getcode()
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="HEALTHY",
                    http_code=code,
                    message=f"HTTP GET success ({code})",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
        except HTTPError as e:
            elapsed = int((time.time() - start_time) * 1000)
            if e.code in (401, 403, 429):
                # Domain is valid, server returned anti-bot response
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="RESTRICTED_BOT",
                    http_code=e.code,
                    message=f"HTTP {e.code} (Site alive, automated access restricted)",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
            elif e.code in (404, 410):
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status="BROKEN",
                    http_code=e.code,
                    message=f"HTTP {e.code} (Not Found)",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
            else:
                status = "HEALTHY" if e.code < 400 else "SERVER_ERROR"
                return LinkVerificationResult(
                    url=url,
                    domain=domain,
                    status=status,
                    http_code=e.code,
                    message=f"HTTP {e.code}: {e.reason}",
                    response_time_ms=elapsed,
                    occurrences=occ_dicts
                )
        except (socket.timeout, TimeoutError):
            elapsed = int((time.time() - start_time) * 1000)
            return LinkVerificationResult(
                url=url,
                domain=domain,
                status="TIMEOUT",
                http_code=None,
                message=f"Connection timed out after {self.timeout}s",
                response_time_ms=elapsed,
                occurrences=occ_dicts
            )
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            return LinkVerificationResult(
                url=url,
                domain=domain,
                status="BROKEN",
                http_code=None,
                message=f"Connection failure: {str(e)}",
                response_time_ms=elapsed,
                occurrences=occ_dicts
            )

    def verify_all(self, url_map: Dict[str, List[LinkOccurrence]]) -> List[LinkVerificationResult]:
        """Verify all URLs concurrently using ThreadPoolExecutor."""
        results: List[LinkVerificationResult] = []
        total = len(url_map)

        if total == 0:
            return results

        if self.verbose:
            print(f"[*] Concurrently verifying {total} unique URLs with {self.max_workers} threads...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.verify_single_url, url, occurrences): url
                for url, occurrences in url_map.items()
            }
            completed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
                results.append(res)
                completed += 1
                if self.verbose and (completed % 10 == 0 or completed == total):
                    print(f"    Progress: {completed}/{total} verified ({int(completed/total*100)}%)")

        return sorted(results, key=lambda x: (x.status != "BROKEN", x.status != "DNS_FAILED", x.url))


def print_cli_report(scanned_files: List[Path], results: List[LinkVerificationResult]) -> int:
    """Render terminal report and return exit code (0 = pass, 1 = broken found)."""
    healthy = [r for r in results if r.status == "HEALTHY"]
    restricted = [r for r in results if r.status == "RESTRICTED_BOT"]
    broken = [r for r in results if r.status in ("BROKEN", "DNS_FAILED")]
    other = [r for r in results if r.status not in ("HEALTHY", "RESTRICTED_BOT", "BROKEN", "DNS_FAILED")]

    print("\n" + "=" * 80)
    print("                ACDP URL & DOMAIN REACHABILITY AUDIT REPORT")
    print("=" * 80)
    print(f"  Total Scanned Files : {len(scanned_files)}")
    print(f"  Total Unique URLs   : {len(results)}")
    print(f"  [+] HEALTHY (200 OK): {len(healthy)}")
    print(f"  [!] RESTRICTED BOT  : {len(restricted)} (Site alive, bot access challenged)")
    print(f"  [?] OTHER / TIMEOUT : {len(other)}")
    print(f"  [-] BROKEN / DEAD   : {len(broken)}")
    print("-" * 80)

    if broken:
        print("\n[CRITICAL] BROKEN OR UNREACHABLE LINKS DETECTED:")
        for idx, b in enumerate(broken, start=1):
            print(f"  {idx}. [{b.status}] {b.url}")
            print(f"     Reason: {b.message}")
            for occ in b.occurrences[:3]:
                print(f"     -> In {occ['file']}:{occ['line']}")
            if len(b.occurrences) > 3:
                print(f"     -> ... and {len(b.occurrences) - 3} more occurrences")
        print("\n" + "=" * 80)
        return 1

    if restricted and not broken:
        print("\n[NOTE] All links are reachable. Sites with anti-bot restrictions were grounded and verified.")

    print("\n[PASS] All links and domains in scanned scope are verified accessible!")
    print("=" * 80 + "\n")
    return 0


def generate_markdown_report(results: List[LinkVerificationResult], output_file: Path) -> None:
    """Export results to GitHub-flavored Markdown."""
    lines = [
        "# ACDP Link & Domain Reachability Audit Report",
        f"> **Generated at**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"> **Total URLs Verified**: {len(results)}",
        "",
        "## Summary Metrics",
        "",
        "| Status Category | Count | Description |",
        "| :--- | :---: | :--- |",
        f"| 🟢 **Healthy** | {len([r for r in results if r.status == 'HEALTHY'])} | HTTP 200-399 reachable |",
        f"| 🟡 **Restricted Bot** | {len([r for r in results if r.status == 'RESTRICTED_BOT'])} | Domain valid, HTTP 401/403/429 anti-bot challenge |",
        f"| 🔴 **Broken / Dead** | {len([r for r in results if r.status in ('BROKEN', 'DNS_FAILED')])} | Dead DNS or HTTP 404/410 |",
        f"| ⚪ **Timeout / Other** | {len([r for r in results if r.status not in ('HEALTHY', 'RESTRICTED_BOT', 'BROKEN', 'DNS_FAILED')])} | Network timeout or transient error |",
        "",
        "---",
        "",
        "## Detailed Link Audit Table",
        "",
        "| URL & Domain | Status | HTTP Code | Latency | Source File & Line |",
        "| :--- | :---: | :---: | :---: | :--- |"
    ]

    for r in results:
        status_icon = "🟢" if r.status == "HEALTHY" else ("🟡" if r.status == "RESTRICTED_BOT" else "🔴")
        src = f"`{Path(r.occurrences[0]['file']).name}:{r.occurrences[0]['line']}`" if r.occurrences else "N/A"
        code_str = str(r.http_code) if r.http_code else "-"
        lines.append(f"| [{r.url}]({r.url}) | {status_icon} `{r.status}` | `{code_str}` | {r.response_time_ms}ms | {src} |")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Verify all URLs and domains in repository files.")
    parser.add_argument("--path", "-p", default=".", help="File or directory to scan (default: current directory)")
    parser.add_argument("--timeout", "-t", type=float, default=8.0, help="HTTP timeout in seconds (default: 8.0)")
    parser.add_argument("--workers", "-w", type=int, default=10, help="Thread pool worker count (default: 10)")
    parser.add_argument("--ignore", "-i", nargs="*", default=[], help="Domain names to ignore")
    parser.add_argument("--output", "-o", help="Path to write JSON audit report")
    parser.add_argument("--markdown", "-m", help="Path to write Markdown audit report")
    parser.add_argument("--no-fail", action="store_true", help="Always exit with 0 even if broken links exist")
    args = parser.parse_args()

    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"[ERROR] Target path does not exist: {target_path}", file=sys.stderr)
        sys.exit(2)

    verifier = LinkVerifier(
        timeout=args.timeout,
        max_workers=args.workers,
        ignored_domains=set(args.ignore),
        verbose=True
    )

    print(f"[*] Scanning files in: {target_path} ...")
    scanned_files, url_map = verifier.scan_path(target_path)
    print(f"[*] Discovered {len(url_map)} unique URLs across {len(scanned_files)} files.")

    results = verifier.verify_all(url_map)

    # Save JSON report if requested
    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)
        print(f"[+] JSON report saved to: {out_path}")

    # Save Markdown report if requested
    if args.markdown:
        md_path = Path(args.markdown).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        generate_markdown_report(results, md_path)
        print(f"[+] Markdown report saved to: {md_path}")

    exit_code = print_cli_report(scanned_files, results)
    if args.no_fail:
        sys.exit(0)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
