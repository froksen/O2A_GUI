import datetime as dt
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "aula" / "timezone_utils.py"
SPEC = importlib.util.spec_from_file_location("timezone_utils", MODULE_PATH)
timezone_utils = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(timezone_utils)

format_aula_datetime = timezone_utils.format_aula_datetime
get_aula_utc_offset = timezone_utils.get_aula_utc_offset


def test_copenhagen_offsets_cover_2026_boundaries():
    assert get_aula_utc_offset(dt.datetime(2026, 3, 28, 12, 0, 0)) == "+01:00"
    assert get_aula_utc_offset(dt.datetime(2026, 3, 29, 12, 0, 0)) == "+02:00"
    assert get_aula_utc_offset(dt.datetime(2026, 7, 15, 12, 0, 0)) == "+02:00"
    assert get_aula_utc_offset(dt.datetime(2026, 10, 25, 12, 0, 0)) == "+01:00"


def test_aula_datetime_formatter_uses_dynamic_offset():
    assert (
        format_aula_datetime(dt.datetime(2026, 7, 15, 8, 30, 0))
        == "2026-07-15T08:30:00+02:00"
    )
    assert (
        format_aula_datetime(dt.datetime(2026, 12, 15, 8, 30, 0))
        == "2026-12-15T08:30:00+01:00"
    )
