#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_ai_slop.py - Deterministic AI Slop & Tropes Detector for ACDP Platform
Part of 'anti-slop-scientific-writer' skill.

Scans Markdown (.md), HTML (.html), and plain text files for:
1. Banned AI fluff vocabulary (English & Vietnamese).
2. Structural tropes (negative parallelism, em-dash addiction, sycophancy, tie-backs, fractal conclusions).
3. Formatting artifacts (monotonous bold-first bullets, announce-then-answer preambles).
4. Calculates a Slop Index (0-100) and outputs clean, actionable audit reports.
"""

import os
import sys
import re
import argparse
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ==============================================================================
# 1. BANNED VOCABULARY CATALOG (ENGLISH & VIETNAMESE)
# ==============================================================================

BANNED_WORDS_EN = {
    # Grandiose / Ornate Nouns
    "tapestry": "interconnected structure, system, network, or synthesis",
    "landscape": "domain, field, sector, or context",
    "testament": "evidence, proof, demonstration, or indicator",
    "beacon": "model, standard, reference, or guide",
    "paradigm": "model, framework, or methodology",
    "synergy": "cooperation, joint effect, or integration",
    "game-changer": "significant improvement or substantial shift",
    "touchstone": "criterion or standard",

    # Overused "AI" Verbs
    "delve": "examine, investigate, analyze, study, or explore",
    "embark": "begin, start, initiate, or commence",
    "foster": "support, encourage, promote, or develop",
    "elevate": "improve, increase, heighten, or upgrade",
    "streamline": "simplify, optimize, or accelerate",
    "harness": "use, apply, utilize, or employ",
    "revolutionize": "transform, substantially alter, or modernize",
    "unravel": "clarify, explain, or decompose",
    "demystify": "explain, clarify, or define",
    "underscore": "emphasize, highlight, or note",

    # Empty Adjectives & Adverbs
    "paramount": "important, central, or critical",
    "pivotal": "important, key, or decisive",
    "crucial": "important, required, or essential",
    "vital": "necessary, essential, or important",
    "robust": "resilient, reliable, or well-tested (specify exact metrics)",
    "seamless": "integrated, continuous, or low-latency",
    "groundbreaking": "new, first, or unprecedented",
    "breathtaking": "significant or large",
    "meticulous": "careful, structured, or thorough",
    "multifaceted": "complex or having multiple aspects",
    "intertwined": "connected or related",
    "quietly": "remove or state the exact mechanism",
    "deeply": "remove or state quantitative degree",
    "fundamentally": "remove or explain technical basis",
    "remarkably": "remove or quantify",
    "arguably": "remove or cite specific evidence",
}

BANNED_WORDS_VI = {
    # Từ ngữ sáo rỗng thường gặp trong văn bản AI dịch/sinh
    "đi sâu vào": "phân tích, khảo sát, kiểm tra, nghiên cứu",
    "bức tranh toàn cảnh": "bối cảnh, tổng quan, phạm vi",
    "minh chứng cho": "bằng chứng của, chứng minh rằng",
    "ngọn hải đăng": "mô hình mẫu, chuẩn đối sánh",
    "hành trình": "quá trình, giai đoạn, chu kỳ",
    "bước ngoặt": "cải tiến lớn, sự thay đổi",
    "đóng vai trò then chốt": "cần thiết cho, quyết định",
    "đóng vai trò quan trọng": "ảnh hưởng trực tiếp đến, cần thiết",
    "giải pháp toàn diện": "hệ thống, kiến trúc (nêu rõ phạm vi cụ thể)",
    "vượt trội": "cao hơn X% (nêu số liệu đo đạc)",
    "tối ưu hóa vượt bậc": "tối ưu, cải thiện (kèm số liệu)",
    "hãy cùng khám phá": "bỏ câu chào rào đón, đi thẳng vào nội dung",
    "chắc chắn rồi": "bỏ câu xã giao, trả lời trực diện",
    "như chúng ta đã biết": "loại bỏ (dẫn chứng nguồn cụ thể)",
    "đáng chú ý là": "loại bỏ từ nối rào đón",
    "không thể phủ nhận rằng": "loại bỏ từ đệm",
    "mảnh ghép quan trọng": "thành phần, module",
}

# ==============================================================================
# 2. STRUCTURAL PATTERN DETECTORS (REGEX TROPES)
# ==============================================================================

STRUCTURAL_RULES = [
    {
        "id": "T01-NEGATIVE-PARALLELISM-EN",
        "name": "Negative Parallelism (EN)",
        "pattern": re.compile(r"\b(?:it(?:'s| is)|the (?:goal|question|issue|challenge)) not\s+[^.!?\n]{2,50}[,;—–-]\s*(?:it(?:'s| is)|but|rather|instead)\b", re.IGNORECASE),
        "description": "Banned trope 'It's not X -- it's Y'. State the proposition directly without artificial dramatic contrast.",
        "penalty": 15,
        "suggestion": "Express the positive claim directly. E.g., replace 'It is not a bug, it is a design flaw' with 'This is a fundamental design flaw.'"
    },
    {
        "id": "T01-NEGATIVE-PARALLELISM-VI",
        "name": "Negative Parallelism (VI)",
        "pattern": re.compile(r"\bkhông\s+phải\s+[^,.!?\n]{2,40}[,;—–-]\s*mà\s+(?:là|ở chỗ)\b", re.IGNORECASE),
        "description": "Mẫu câu giả tạo 'Không phải X, mà là Y'. Hãy khẳng định trực tiếp nội dung cốt lõi.",
        "penalty": 15,
        "suggestion": "Viết thẳng luận điểm thực tế thay vì phủ định giả tạo. Ví dụ: thay 'Không phải lỗi code, mà là lỗi kiến trúc' thành 'Đây là lỗi thuộc tầng kiến trúc.'"
    },
    {
        "id": "T02-SYCOPHANCY-OPENING",
        "name": "Sycophantic Conversational Preamble",
        "pattern": re.compile(r"^(?:great question|certainly|sure thing|absolutely|i'd be happy to|chắc chắn rồi|rất vui được giúp|câu hỏi rất hay|tất nhiên rồi)[!.,]", re.IGNORECASE | re.MULTILINE),
        "description": "Sycophantic filler opening. Eliminate fake politeness and lead immediately with the factual answer.",
        "penalty": 12,
        "suggestion": "Cut opening chatter completely. Begin sentence 1 with the direct solution or conclusion."
    },
    {
        "id": "T03-ANNOUNCE-THEN-ANSWER",
        "name": "Announce-Then-Answer Preamble",
        "pattern": re.compile(r"\b(?:in this section[, ]+we will (?:delve|explore|examine)|dưới đây là (?:các|những) (?:bước|chi tiết|thông tin)|sau đây tôi sẽ trình bày|let's break this down|let's unpack this)\b", re.IGNORECASE),
        "description": "Throat-clearing / announce-then-answer preamble. Deliver the content directly without narrating what will follow.",
        "penalty": 10,
        "suggestion": "Delete the meta-announcement. Start immediately with the headers or content items."
    },
    {
        "id": "T04-SIGNPOSTED-CONCLUSION",
        "name": "Signposted Fractal Conclusion",
        "pattern": re.compile(r"(?:^|\n)#{1,4}\s*(?:in conclusion|to sum up|in summary|tóm lại|kết luận lại)\b|\b(?:in conclusion[, ]|to sum up[, ]|in summary[, ]|tóm lại là[, ]|kết luận lại là)\b", re.IGNORECASE),
        "description": "Mechanical 'In conclusion / Tóm lại' signpost. Scientific papers and technical docs land points cleanly without redundant summaries.",
        "penalty": 12,
        "suggestion": "Remove the redundant wrap-up heading or integrate the final actionable takeaway directly."
    },
    {
        "id": "T05-THE-TIE-BACK",
        "name": "The Tie-Back Echo",
        "pattern": re.compile(r"\b(?:so[, ]+to answer your question|to bring it back to what you asked|như vậy[, ]+để trả lời câu hỏi của bạn)\b", re.IGNORECASE),
        "description": "The Tie-Back: Restating the original prompt back to the reader at the end of the text.",
        "penalty": 10,
        "suggestion": "Remove the tie-back loop. End immediately once the final technical step is delivered."
    },
    {
        "id": "T06-HYPOPHORA-DRAMA",
        "name": "Manufactured Rhetorical Question (Hypophora)",
        "pattern": re.compile(r"\b(?:the result\?|the catch\?|the best part\?|the question is\?|kết quả là gì\?|điều đáng nói ở đây là gì\?)\s+[A-ZÀ-Ỹ0-9]", re.IGNORECASE),
        "description": "Self-posed rhetorical question answered immediately for theatrical drama. Unsuited for rigorous scientific prose.",
        "penalty": 10,
        "suggestion": "State the finding or consequence directly as a factual declarative sentence."
    },
    {
        "id": "T07-REASONING-LEAK",
        "name": "LLM Reasoning / Deliberation Leak",
        "pattern": re.compile(r"\b(?:i need to be (?:careful|exact) about|what that changes in the design is|tôi cần phải làm rõ rằng|tôi sẽ phân tích theo các bước sau)\b", re.IGNORECASE),
        "description": "Reasoning leak: Unprompted narration of internal deliberation or agent planning inside final user output.",
        "penalty": 14,
        "suggestion": "Keep internal deliberation in private thinking. Only emit the final verified artifact or answer."
    },
    {
        "id": "T08-INVENTED-LABELS",
        "name": "Invented Concept Labels",
        "pattern": re.compile(r"\b(?:supervision paradox|acceleration trap|workload creep|retrieval debt|prompt debt|nghịch lý giám sát|bẫy tăng tốc)\b", re.IGNORECASE),
        "description": "Invented buzzword compound labels created to manufacture artificial analytical profundity.",
        "penalty": 10,
        "suggestion": "Describe the concrete engineering problem using established industry terminology."
    }
]

# ==============================================================================
# 3. AUDIT ENGINE
# ==============================================================================

@dataclass
class SlopViolation:
    file_path: str
    line_number: int
    rule_id: str
    category: str
    matched_text: str
    context: str
    suggestion: str
    penalty: int

@dataclass
class AuditReport:
    file_path: str
    total_lines: int
    total_words: int
    violations: List[SlopViolation]
    slop_score: int  # 0 to 100 (0 = clean, 100 = pure slop)
    is_clean: bool

class SlopDetector:
    def __init__(self, em_dash_threshold_per_block: int = 2):
        self.em_dash_threshold = em_dash_threshold_per_block

    def analyze_text(self, text: str, file_path: str = "input_text") -> AuditReport:
        lines = text.splitlines()
        total_words = len(re.findall(r"\b\w+\b", text))
        violations: List[SlopViolation] = []

        # 1. Scan Line by Line for Banned Words (excluding code blocks and inline code)
        in_code_block = False
        for line_idx, line in enumerate(lines, start=1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Strip inline code spans like `delve` or `code_symbol`
            clean_line = re.sub(r"`[^`]+`", "", line)

            # English Banned Words
            for word, repl in BANNED_WORDS_EN.items():
                pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
                for match in pattern.finditer(clean_line):
                    start = max(0, match.start() - 25)
                    end = min(len(clean_line), match.end() + 25)
                    ctx = clean_line[start:end].strip()
                    violations.append(SlopViolation(
                        file_path=file_path,
                        line_number=line_idx,
                        rule_id="W-BANNED-WORD-EN",
                        category="Vocabulary Slop",
                        matched_text=match.group(0),
                        context=f"...{ctx}...",
                        suggestion=f"Replace '{match.group(0)}' with: {repl}",
                        penalty=4
                    ))

            # Vietnamese Banned Words
            for word, repl in BANNED_WORDS_VI.items():
                pattern = re.compile(rf"(?<!\w){re.escape(word)}(?!\w)", re.IGNORECASE)
                for match in pattern.finditer(clean_line):
                    start = max(0, match.start() - 25)
                    end = min(len(clean_line), match.end() + 25)
                    ctx = clean_line[start:end].strip()
                    violations.append(SlopViolation(
                        file_path=file_path,
                        line_number=line_idx,
                        rule_id="W-BANNED-WORD-VI",
                        category="Vocabulary Slop (VI)",
                        matched_text=match.group(0),
                        context=f"...{ctx}...",
                        suggestion=f"Thay thế '{match.group(0)}' bằng: {repl}",
                        penalty=5
                    ))

        # 2. Scan Structural Tropes Across Entire Content
        for rule in STRUCTURAL_RULES:
            for match in rule["pattern"].finditer(text):
                char_idx = match.start()
                line_no = text[:char_idx].count("\n") + 1
                matched_snippet = match.group(0).strip().replace("\n", " ")
                if len(matched_snippet) > 60:
                    matched_snippet = matched_snippet[:57] + "..."

                violations.append(SlopViolation(
                    file_path=file_path,
                    line_number=line_no,
                    rule_id=rule["id"],
                    category="Structural Trope",
                    matched_text=matched_snippet,
                    context=matched_snippet,
                    suggestion=rule["suggestion"],
                    penalty=rule["penalty"]
                ))

        # 3. Check for Em-dash Addiction per Paragraph (excluding code blocks and markdown tables)
        clean_text_for_dashes = re.sub(r"```[\s\S]*?```", "", text)
        clean_paragraphs = clean_text_for_dashes.split("\n\n")
        curr_char = 0
        for p in clean_paragraphs:
            # Filter out table formatting lines like | :--- |
            p_lines = [l for l in p.splitlines() if not re.match(r"^\|?\s*[-:]+[-| :]*\|?$", l.strip())]
            p_clean = "\n".join(p_lines)
            
            # Count actual em dashes (—) or standalone spaced/parenthetical dashes ( -- ), not inline markdown syntax
            em_dash_count = len(re.findall(r"(?:—|\s--\s)", p_clean))
            if em_dash_count > self.em_dash_threshold:
                line_no = text[:curr_char].count("\n") + 1
                sample = p_clean.strip().replace("\n", " ")[:80]
                violations.append(SlopViolation(
                    file_path=file_path,
                    line_number=line_no,
                    rule_id="F-EM-DASH-ADDICTION",
                    category="Formatting Trope",
                    matched_text=f"{em_dash_count} em-dashes in single paragraph",
                    context=f"{sample}...",
                    suggestion="Reduce em-dash frequency. Use periods, commas, or parentheses instead of dramatic dash pauses.",
                    penalty=8
                ))
            curr_char += len(p) + 2

        # 4. Check for Monotonous Bold-First Bullets
        bullet_lines = [l.strip() for l in lines if re.match(r"^[-*+]\s+", l.strip())]
        if len(bullet_lines) >= 4:
            bold_count = sum(1 for b in bullet_lines if re.match(r"^[-*+]\s+\*\*[^*]+\*\*", b))
            if bold_count / len(bullet_lines) >= 0.85:
                violations.append(SlopViolation(
                    file_path=file_path,
                    line_number=1,
                    rule_id="F-BOLD-FIRST-BULLETS",
                    category="Formatting Trope",
                    matched_text=f"{bold_count}/{len(bullet_lines)} bullets start with bold words",
                    context="Monotonous **bold keyword**: syntax throughout bullet list.",
                    suggestion="Vary list item structure. Use natural narrative phrasing or markdown tables for key-value data.",
                    penalty=6
                ))

        # Calculate Normalized Slop Score (0 - 100)
        total_penalties = sum(v.penalty for v in violations)
        word_norm = max(100, total_words) / 300.0  # normalize per ~300 words
        raw_score = total_penalties / word_norm
        slop_score = min(100, int(round(raw_score)))

        return AuditReport(
            file_path=file_path,
            total_lines=len(lines),
            total_words=total_words,
            violations=violations,
            slop_score=slop_score,
            is_clean=(len(violations) == 0)
        )

    def analyze_file(self, file_path: str) -> AuditReport:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return self.analyze_text(content, file_path=file_path)

# ==============================================================================
# 4. CLI INTERFACE
# ==============================================================================

def print_text_report(report: AuditReport, show_suggestions: bool = True):
    print("=" * 80)
    print(f"AUDIT REPORT: {report.file_path}")
    print(f"Stats: {report.total_lines} lines | {report.total_words} words | Violations: {len(report.violations)}")
    
    score = report.slop_score
    if score == 0:
        verdict = "PRISTINE SCIENTIFIC PROSE (0/100)"
    elif score <= 15:
        verdict = f"ACCEPTABLE / MINOR FLUFF ({score}/100)"
    elif score <= 40:
        verdict = f"ELEVATED AI SLOP ({score}/100) - REVISION RECOMMENDED"
    else:
        verdict = f"HEAVY AI SLOP ({score}/100) - REWRITE REQUIRED"

    print(f"Slop Index: {verdict}")
    print("=" * 80)

    if not report.violations:
        print("No AI slop or tropes detected. Clean scientific style maintained!\n")
        return

    print(f"{'LINE':<6} | {'RULE ID':<26} | {'VIOLATION SNIPPET'}")
    print("-" * 80)
    for v in report.violations:
        print(f"L{v.line_number:<5} | {v.rule_id:<26} | {v.matched_text}")
        if show_suggestions:
            print(f"       Sua: {v.suggestion}")
            print(f"       Doan: {v.context}")
            print("-" * 80)
    print()

def main():
    parser = argparse.ArgumentParser(
        description="ACDP Anti-Slop & Scientific Writing Linter"
    )
    parser.add_argument("target", help="File path or directory to scan (.md, .html, .txt)")
    parser.add_argument("--strict", action="store_true", help="Exit code 1 if any violation or slop score > 0")
    parser.add_argument("--threshold", type=int, default=10, help="Slop score threshold for exit code 1 (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--no-suggestions", action="store_true", help="Hide remediation suggestions")

    args = parser.parse_args()

    detector = SlopDetector()
    targets = []

    if os.path.isfile(args.target):
        targets.append(args.target)
    elif os.path.isdir(args.target):
        for root, _, files in os.walk(args.target):
            for f in files:
                if f.endswith((".md", ".html", ".txt")):
                    targets.append(os.path.join(root, f))
    else:
        print(f"Error: Target path '{args.target}' does not exist.", file=sys.stderr)
        sys.exit(2)

    all_reports: List[AuditReport] = []
    has_failure = False

    for path in targets:
        report = detector.analyze_file(path)
        all_reports.append(report)
        if args.strict and not report.is_clean:
            has_failure = True
        elif report.slop_score > args.threshold:
            has_failure = True

    if args.json:
        data = [
            {
                "file_path": r.file_path,
                "lines": r.total_lines,
                "words": r.total_words,
                "slop_score": r.slop_score,
                "is_clean": r.is_clean,
                "violations": [asdict(v) for v in r.violations]
            }
            for r in all_reports
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for r in all_reports:
            print_text_report(r, show_suggestions=not args.no_suggestions)

    if has_failure:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
