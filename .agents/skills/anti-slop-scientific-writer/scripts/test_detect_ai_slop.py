#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_detect_ai_slop.py - Unit tests for detect_ai_slop.py linter
"""

import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detect_ai_slop import SlopDetector, AuditReport

class TestSlopDetector(unittest.TestCase):
    def setUp(self):
        self.detector = SlopDetector()

    def test_clean_scientific_text(self):
        clean_text = (
            "We evaluate the hybrid retrieval pipeline on a dataset of 1,200 competition documents. "
            "The system combines BM25 keyword matching with dense embeddings indexed in Qdrant. "
            "Empirical results show a Mean Reciprocal Rank (MRR@10) of 0.84 and a p95 query latency of 112 ms."
        )
        report = self.detector.analyze_text(clean_text)
        self.assertTrue(report.is_clean)
        self.assertEqual(report.slop_score, 0)
        self.assertEqual(len(report.violations), 0)

    def test_english_slop_words(self):
        slop_text = (
            "In this research, we delve into the complex landscape of AI models. "
            "This work is a testament to the robust synergy of neural networks."
        )
        report = self.detector.analyze_text(slop_text)
        self.assertFalse(report.is_clean)
        self.assertGreater(report.slop_score, 0)
        rule_ids = [v.rule_id for v in report.violations]
        self.assertIn("W-BANNED-WORD-EN", rule_ids)
        matched_words = [v.matched_text.lower() for v in report.violations]
        self.assertIn("delve", matched_words)
        self.assertIn("landscape", matched_words)
        self.assertIn("testament", matched_words)

    def test_vietnamese_slop_words(self):
        slop_text = (
            "Bài báo này sẽ đi sâu vào việc phân tích bức tranh toàn cảnh của hệ thống. "
            "Đây là minh chứng cho một giải pháp toàn diện và vượt trội."
        )
        report = self.detector.analyze_text(slop_text)
        self.assertFalse(report.is_clean)
        rule_ids = [v.rule_id for v in report.violations]
        self.assertIn("W-BANNED-WORD-VI", rule_ids)
        matched_words = [v.matched_text.lower() for v in report.violations]
        self.assertTrue(any("đi sâu vào" in m for m in matched_words))
        self.assertTrue(any("bức tranh toàn cảnh" in m for m in matched_words))

    def test_negative_parallelism(self):
        text_en = "It is not a simple script, but rather a complete operating system."
        report_en = self.detector.analyze_text(text_en)
        rule_ids_en = [v.rule_id for v in report_en.violations]
        self.assertIn("T01-NEGATIVE-PARALLELISM-EN", rule_ids_en)

        text_vi = "Đây không phải là một lỗi cú pháp, mà là vấn đề logic."
        report_vi = self.detector.analyze_text(text_vi)
        rule_ids_vi = [v.rule_id for v in report_vi.violations]
        self.assertIn("T01-NEGATIVE-PARALLELISM-VI", rule_ids_vi)

    def test_sycophancy_opening(self):
        text = "Great question! We can configure DuckDB by setting the memory limit parameter."
        report = self.detector.analyze_text(text)
        rule_ids = [v.rule_id for v in report.violations]
        self.assertIn("T02-SYCOPHANCY-OPENING", rule_ids)

    def test_signposted_conclusion(self):
        text = "### In conclusion\nThe pipeline achieved target performance metrics."
        report = self.detector.analyze_text(text)
        rule_ids = [v.rule_id for v in report.violations]
        self.assertIn("T04-SIGNPOSTED-CONCLUSION", rule_ids)

if __name__ == "__main__":
    unittest.main()
