"""
Unit tests for time format utility.
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st

from utils.time_format_util import TimeFormatUtil


class TestTimeFormatUtil:
    """Test suite for time format utilities."""

    def test_format_time_with_datetime(self):
        """Test formatting datetime object."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = TimeFormatUtil.format_time(dt)
        assert result == '2024-01-15 10:30:45'

    def test_format_time_with_string(self):
        """Test formatting time string."""
        time_str = '2024-01-15 10:30:45'
        result = TimeFormatUtil.format_time(time_str)
        assert result == '2024-01-15 10:30:45'

    def test_format_time_custom_format(self):
        """Test custom datetime formatting."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = TimeFormatUtil.format_time(dt, '%Y/%m/%d')
        assert result == '2024/01/15'

    def test_parse_date(self):
        """Test date parsing."""
        dt_str = '2024-01-15 10:30:45'
        result = TimeFormatUtil.parse_date(dt_str)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_format_time_dict(self):
        """Test formatting time dictionary."""
        time_dict = {
            'created_at': datetime(2024, 1, 15, 10, 30, 45),
            'name': 'test'
        }
        result = TimeFormatUtil.format_time_dict(time_dict)
        assert result['created_at'] == '2024-01-15 10:30:45'
        assert result['name'] == 'test'

    def test_format_time_dict_nested(self):
        """Test formatting nested time dictionary."""
        time_dict = {
            'data': {
                'created_at': datetime(2024, 1, 15, 10, 30, 45)
            }
        }
        result = TimeFormatUtil.format_time_dict(time_dict)
        assert result['data']['created_at'] == '2024-01-15 10:30:45'

    def test_format_time_list(self):
        """Test formatting time list."""
        time_list = [
            datetime(2024, 1, 15, 10, 30, 45),
            '2024-01-16 10:30:45'
        ]
        result = TimeFormatUtil.format_time_list(time_list)
        assert result[0] == '2024-01-15 10:30:45'
        assert result[1] == '2024-01-16 10:30:45'

    def test_format_time_list_with_dicts(self):
        """Test formatting list containing dictionaries."""
        time_list = [
            {'created_at': datetime(2024, 1, 15, 10, 30, 45)},
            {'created_at': datetime(2024, 1, 16, 10, 30, 45)}
        ]
        result = TimeFormatUtil.format_time_list(time_list)
        assert result[0]['created_at'] == '2024-01-15 10:30:45'
        assert result[1]['created_at'] == '2024-01-16 10:30:45'

    def test_format_time_invalid_string(self):
        """Test formatting invalid time string returns original."""
        invalid_str = 'not a date'
        result = TimeFormatUtil.format_time(invalid_str)
        assert result == invalid_str

    def test_parse_date_invalid_string(self):
        """Test parsing invalid date string returns original."""
        invalid_str = 'not a date'
        result = TimeFormatUtil.parse_date(invalid_str)
        assert result == invalid_str

