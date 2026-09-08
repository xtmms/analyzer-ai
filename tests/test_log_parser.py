"""Test delle funzioni pure di core/log_parser.py."""
from core.log_parser import (
    dedupe_entries,
    detect_severity,
    filter_entries,
    parse_log_to_entries,
    prepare_entries_for_send,
    truncate_entry_text,
)


def test_detect_severity_basic():
    assert detect_severity("2026-01-01 CRITICAL something broke") == "CRITICAL"
    assert detect_severity("2026-01-01 ERROR bad thing") == "ERROR"
    assert detect_severity("2026-01-01 WARN low disk") == "WARNING"
    assert detect_severity("2026-01-01 INFO all good") == "INFO"
    assert detect_severity("2026-01-01 just some text") == "INFO"


def test_detect_severity_traceback_is_error():
    assert detect_severity("Traceback (most recent call last):") == "ERROR"


def test_parse_log_groups_python_traceback():
    log = (
        "2026-01-01 10:00:00 INFO starting up\n"
        "2026-01-01 10:00:01 ERROR request failed\n"
        "Traceback (most recent call last):\n"
        '  File "app.py", line 10, in <module>\n'
        "    raise ValueError('boom')\n"
        "ValueError: boom\n"
        "2026-01-01 10:00:02 INFO next line after traceback\n"
    )
    entries = parse_log_to_entries(log)

    # info, error, traceback (raggruppata in una sola entry multi-riga), info
    assert len(entries) == 4
    assert entries[0]["severity"] == "INFO" and entries[0]["is_traceback"] is False
    assert entries[1]["severity"] == "ERROR" and entries[1]["is_traceback"] is False
    assert entries[2]["is_traceback"] is True
    assert entries[2]["severity"] == "ERROR"
    assert "ValueError: boom" in entries[2]["text"]
    assert entries[3]["is_traceback"] is False


def test_filter_entries_by_severity():
    entries = [
        {"text": "a", "severity": "ERROR", "is_traceback": False},
        {"text": "b", "severity": "INFO", "is_traceback": False},
    ]
    filtered = filter_entries(entries, ["ERROR"], "")
    assert len(filtered) == 1
    assert filtered[0]["text"] == "a"


def test_filter_entries_by_regex():
    entries = [
        {"text": "user 42 logged in", "severity": "INFO", "is_traceback": False},
        {"text": "user 43 logged in", "severity": "INFO", "is_traceback": False},
    ]
    filtered = filter_entries(entries, ["INFO"], r"user 4[2]")
    assert len(filtered) == 1
    assert "42" in filtered[0]["text"]


def test_dedupe_entries_collapses_repeated_lines_ignoring_timestamp():
    entries = [
        {"text": "2026-01-01 10:00:00 ERROR healthcheck failed", "severity": "ERROR", "is_traceback": False},
        {"text": "2026-01-01 10:00:01 ERROR healthcheck failed", "severity": "ERROR", "is_traceback": False},
        {"text": "2026-01-01 10:00:02 ERROR healthcheck failed", "severity": "ERROR", "is_traceback": False},
        {"text": "2026-01-01 10:00:03 INFO something else", "severity": "INFO", "is_traceback": False},
    ]
    deduped = dedupe_entries(entries)
    assert len(deduped) == 2
    assert deduped[0]["count"] == 3
    assert "x3" in deduped[0]["text"]
    assert deduped[1]["count"] == 1


def test_dedupe_entries_does_not_merge_different_lines():
    entries = [
        {"text": "ERROR one", "severity": "ERROR", "is_traceback": False},
        {"text": "ERROR two", "severity": "ERROR", "is_traceback": False},
    ]
    deduped = dedupe_entries(entries)
    assert len(deduped) == 2


def test_truncate_entry_text_keeps_head_and_tail():
    text = "A" * 3000
    truncated = truncate_entry_text(text, max_chars=100)
    assert len(truncated) < len(text)
    assert truncated.startswith("A")
    assert truncated.endswith("A")
    assert "troncati" in truncated


def test_truncate_entry_text_noop_below_limit():
    text = "short line"
    assert truncate_entry_text(text, max_chars=2000) == text


def test_prepare_entries_for_send_pipeline():
    entries = [
        {"text": "2026-01-01 10:00:00 ERROR boom", "severity": "ERROR", "is_traceback": False},
        {"text": "2026-01-01 10:00:01 ERROR boom", "severity": "ERROR", "is_traceback": False},
    ]
    result = prepare_entries_for_send(entries, dedupe=True)
    assert len(result) == 1
    assert "x2" in result[0]

    result_no_dedupe = prepare_entries_for_send(entries, dedupe=False)
    assert len(result_no_dedupe) == 2

def test_parse_junit_xml():
    xml_data = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="test_foo" name="test_bar">
      <failure message="AssertionError: assert False">
        Traceback (most recent call last):
          File "test_foo.py", line 4, in test_bar
            assert False
      </failure>
    </testcase>
  </testsuite>
</testsuites>"""
    entries = parse_log_to_entries(xml_data)
    assert len(entries) == 1
    assert "test_foo.test_bar" in entries[0]["text"]
    assert entries[0]["severity"] == "ERROR"
    assert entries[0]["is_traceback"] is True

def test_parse_test_json():
    json_data = """
    {
      "tests": [
        {
          "title": "should fail",
          "status": "failed",
          "err": {
            "message": "Timed out retrying",
            "stack": "Error: Timed out retrying at Context.eval"
          }
        }
      ]
    }
    """
    entries = parse_log_to_entries(json_data)
    assert len(entries) == 1
    assert "should fail" in entries[0]["text"]
    assert "Timed out retrying" in entries[0]["text"]
    assert entries[0]["severity"] == "ERROR"
    assert entries[0]["is_traceback"] is True
