#!/usr/bin/env python3
"""Lock the doctor.py extraction matrix per codex round v0.8.0-r1 Ffalsif.1.

Tests the 4 combinations of (markitdown installed?, legacy CLI installed?)
and asserts the expected tier output for each.
"""
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "allincms-content-ops" / "scripts"))

import doctor  # noqa: E402


def _stub(markitdown, legacy_cli, paddleocr=False):
    """Patch the underscore-prefixed detectors. Returns context-manager-like
    nested mocks via mock.patch.multiple-style."""
    return mock.patch.multiple(
        doctor,
        _has_markitdown=mock.Mock(return_value=markitdown),
        _has_legacy_cli=mock.Mock(return_value=legacy_cli),
        _has_paddleocr=mock.Mock(return_value=paddleocr),
    )


def test_both_installed():
    with _stub(markitdown=True, legacy_cli=True):
        tier, msg, _ = doctor.check_extraction()
        assert tier == "strong"
        assert "markitdown installed" in msg
        assert "fast-path" in msg


def test_only_markitdown():
    with _stub(markitdown=True, legacy_cli=False):
        tier, msg, _ = doctor.check_extraction()
        assert tier == "strong"
        assert "default extractor" in msg


def test_only_legacy():
    with _stub(markitdown=False, legacy_cli=True):
        tier, msg, _ = doctor.check_extraction()
        assert tier == "strong"
        assert "legacy fast-path" in msg
        assert "pipx install markitdown" in msg, "should nudge toward markitdown for Excel coverage"


def test_neither():
    with _stub(markitdown=False, legacy_cli=False):
        tier, msg, _ = doctor.check_extraction()
        assert tier == "degraded"
        assert "no extractor" in msg.lower()


def test_chinese_ocr_always_strong():
    """Per Fclass.1 — paddleocr is optional, never degraded in the summary."""
    with _stub(markitdown=False, legacy_cli=False, paddleocr=False):
        tier, _, _ = doctor.check_chinese_ocr()
        assert tier == "strong"
    with _stub(markitdown=False, legacy_cli=False, paddleocr=True):
        tier, _, _ = doctor.check_chinese_ocr()
        assert tier == "strong"


if __name__ == "__main__":
    test_both_installed()
    test_only_markitdown()
    test_only_legacy()
    test_neither()
    test_chinese_ocr_always_strong()
    print("test_doctor_extraction_matrix: 5/5 passed")
