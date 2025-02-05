import pytest
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interpretNotionPage import (
    extract_table_content,
    parse_time_range,
    get_time_info_without_errors,
    calculate_duration,
    interpret_table_contents
)

def test_extract_table_content():
    html = """
    <title>1</title>
    <table>
        <tr><td>8:00-10:00</td><td>study/work</td></tr>
        <tr><td>10:00-12:00</td><td>meeting</td></tr>
    </table>
    """
    expected = [
        ['1', 'sleep'],
        ['8:00-10:00', 'study/work'],
        ['10:00-12:00', 'meeting']
    ]
    result = extract_table_content(html)
    assert result == expected

@pytest.mark.parametrize("time_str,expected", [
    ("12:00-14:00", ("12:00", "14:00")),
    ("-17:00", ("", "17:00")),
    ("9:00-", ("9:00", "")),
])
def test_parse_time_range(time_str, expected):
    result = parse_time_range(time_str)
    assert result == expected

@pytest.mark.parametrize("time_str,prev_info,expected", [
    ("14:30", None, datetime.strptime("14:30", "%H:%M")),
    ("", datetime.strptime("14:30", "%H:%M"), datetime.strptime("14:30", "%H:%M")),
    ("25:00", None, datetime.strptime("13:00", "%H:%M")),  # Should convert 25 to 13
    ("9", datetime.strptime("14:30", "%H:%M"), datetime.strptime("14:09", "%H:%M")),
])
def test_get_time_info_without_errors(time_str, prev_info, expected):
    result = get_time_info_without_errors(time_str, prev_info)
    if expected is None:
        assert result is None
    else:
        assert result.hour == expected.hour
        assert result.minute == expected.minute

@pytest.mark.parametrize("start,end,expected", [
    (
        datetime.strptime("14:00", "%H:%M"),
        datetime.strptime("16:00", "%H:%M"),
        timedelta(hours=2)
    ),
    (
        datetime.strptime("23:00", "%H:%M"),
        datetime.strptime("01:00", "%H:%M"),
        timedelta(hours=2)
    ),
])
def test_calculate_duration(start, end, expected):
    result = calculate_duration(start, end)
    assert result == expected

def test_interpret_table_contents():
    raw_data = [
        ["8:00-10:00", "study"],
        ["10:00-12:00", "work/meeting"],
        ["12:00-13:00", "lunch"]
    ]
    result = interpret_table_contents(raw_data)
    
    # Check if durations are present for expected categories
    assert '📖academic' in result  # for study
    assert '💰work' in result      # for work/meeting
    assert '🍔food' in result      # for lunch

    # Check specific durations
    assert result['📖academic'] == timedelta(hours=2)  # study: 8:00-10:00
    assert result['🍔food'] == timedelta(hours=1)      # lunch: 12:00-13:00 