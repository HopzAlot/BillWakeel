"""Unit tests for the matching rules in tests/eval/run_extraction_eval.py (SCRUM-32).

These run offline: they only test the comparison helpers, no Gemini calls.
"""

import importlib.util
from pathlib import Path

EVAL_PATH = Path(__file__).resolve().parents[1] / "eval" / "run_extraction_eval.py"
_spec = importlib.util.spec_from_file_location("run_extraction_eval", EVAL_PATH)
evaluation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evaluation)


def test_gas_units_exact_match_passes():
    assert evaluation._field_matches("units_consumed", 0.389, 0.389, "gas")


def test_gas_units_within_last_decimal_passes():
    assert evaluation._field_matches("units_consumed", 0.390, 0.389, "gas")


def test_gas_units_off_by_more_than_tolerance_fails():
    # With the electricity tolerance of 1 this would wrongly pass.
    assert not evaluation._field_matches("units_consumed", 1.440, 0.389, "gas")


def test_electricity_units_keep_tolerance_of_one():
    assert evaluation._field_matches("units_consumed", 146, 145, "electricity")


def test_gas_meter_readings_use_whole_number_tolerance():
    assert evaluation._field_matches("meter_reading_current", 3469000, 3469000, "gas")
    assert not evaluation._field_matches("meter_reading_current", 3469010, 3469000, "gas")


def test_load_samples_gas_returns_only_sngpl():
    names = [name for name, _, _ in evaluation._load_samples("gas")]
    assert names == ["sngpl_001", "sngpl_002", "sngpl_003", "sngpl_004"]


def test_load_samples_all_returns_ten():
    assert len(evaluation._load_samples("all")) == 10