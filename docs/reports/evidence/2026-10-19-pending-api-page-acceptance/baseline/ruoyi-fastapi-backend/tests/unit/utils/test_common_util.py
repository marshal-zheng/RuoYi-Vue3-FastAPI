"""
Unit tests for common utility functions.
"""

import pytest
from hypothesis import given, strategies as st

from utils.common_util import CamelCaseUtil, ObjectUtil, StringUtil


class TestCamelCaseUtil:
    """Test suite for camel case conversion utilities."""

    def test_to_camel_case_basic(self):
        """Test basic snake_case to camelCase conversion."""
        assert CamelCaseUtil.to_camel_case('user_name') == 'userName'
        assert CamelCaseUtil.to_camel_case('user_id') == 'userId'

    def test_to_camel_case_multiple_underscores(self):
        """Test conversion with multiple underscores."""
        assert CamelCaseUtil.to_camel_case('user_first_name') == 'userFirstName'
        assert CamelCaseUtil.to_camel_case('a_b_c_d') == 'aBCD'

    def test_to_camel_case_already_camel(self):
        """Test conversion of already camelCase string."""
        assert CamelCaseUtil.to_camel_case('userName') == 'userName'

    def test_to_camel_case_empty(self):
        """Test conversion of empty string."""
        assert CamelCaseUtil.to_camel_case('') == ''

    def test_to_camel_case_single_word(self):
        """Test conversion of single word."""
        assert CamelCaseUtil.to_camel_case('user') == 'user'

    def test_to_snake_case_basic(self):
        """Test basic camelCase to snake_case conversion."""
        assert CamelCaseUtil.to_snake_case('userName') == 'user_name'
        assert CamelCaseUtil.to_snake_case('userId') == 'user_id'

    def test_to_snake_case_multiple_capitals(self):
        """Test conversion with multiple capital letters."""
        assert CamelCaseUtil.to_snake_case('userFirstName') == 'user_first_name'
        assert CamelCaseUtil.to_snake_case('HTTPResponse') == 'http_response'

    def test_to_snake_case_already_snake(self):
        """Test conversion of already snake_case string."""
        assert CamelCaseUtil.to_snake_case('user_name') == 'user_name'

    def test_to_snake_case_empty(self):
        """Test conversion of empty string."""
        assert CamelCaseUtil.to_snake_case('') == ''

    @given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=20))
    def test_case_conversion_round_trip(self, text: str):
        """Property test: converting to snake and back should preserve meaning."""
        snake = CamelCaseUtil.to_snake_case(text)
        camel = CamelCaseUtil.to_camel_case(snake)
        # Should be similar (case-insensitive)
        assert snake.replace('_', '').lower() == camel.lower()


class TestObjectUtil:
    """Test suite for object utility functions."""

    def test_is_empty_none(self):
        """Test is_empty with None."""
        assert ObjectUtil.is_empty(None) is True

    def test_is_empty_empty_string(self):
        """Test is_empty with empty string."""
        assert ObjectUtil.is_empty('') is True
        assert ObjectUtil.is_empty('  ') is True

    def test_is_empty_empty_list(self):
        """Test is_empty with empty list."""
        assert ObjectUtil.is_empty([]) is True

    def test_is_empty_empty_dict(self):
        """Test is_empty with empty dict."""
        assert ObjectUtil.is_empty({}) is True

    def test_is_empty_non_empty(self):
        """Test is_empty with non-empty values."""
        assert ObjectUtil.is_empty('test') is False
        assert ObjectUtil.is_empty([1, 2, 3]) is False
        assert ObjectUtil.is_empty({'key': 'value'}) is False
        assert ObjectUtil.is_empty(0) is False
        assert ObjectUtil.is_empty(False) is False

    def test_is_not_empty(self):
        """Test is_not_empty function."""
        assert ObjectUtil.is_not_empty('test') is True
        assert ObjectUtil.is_not_empty([1]) is True
        assert ObjectUtil.is_not_empty(None) is False
        assert ObjectUtil.is_not_empty('') is False

    def test_get_nested_value(self):
        """Test getting nested dictionary values."""
        data = {'user': {'name': 'John', 'age': 30}}
        assert ObjectUtil.get_nested_value(data, 'user.name') == 'John'
        assert ObjectUtil.get_nested_value(data, 'user.age') == 30

    def test_get_nested_value_missing(self):
        """Test getting missing nested value."""
        data = {'user': {'name': 'John'}}
        assert ObjectUtil.get_nested_value(data, 'user.email', default='N/A') == 'N/A'

    def test_get_nested_value_none(self):
        """Test getting nested value from None."""
        assert ObjectUtil.get_nested_value(None, 'user.name', default='N/A') == 'N/A'


class TestStringUtil:
    """Test suite for string utility functions."""

    def test_is_blank_none(self):
        """Test is_blank with None."""
        assert StringUtil.is_blank(None) is True

    def test_is_blank_empty(self):
        """Test is_blank with empty string."""
        assert StringUtil.is_blank('') is True
        assert StringUtil.is_blank('   ') is True
        assert StringUtil.is_blank('\t\n') is True

    def test_is_blank_non_empty(self):
        """Test is_blank with non-empty string."""
        assert StringUtil.is_blank('test') is False
        assert StringUtil.is_blank('  test  ') is False

    def test_is_not_blank(self):
        """Test is_not_blank function."""
        assert StringUtil.is_not_blank('test') is True
        assert StringUtil.is_not_blank('') is False
        assert StringUtil.is_not_blank(None) is False

    def test_truncate_basic(self):
        """Test basic string truncation."""
        assert StringUtil.truncate('Hello World', 5) == 'Hello...'
        assert StringUtil.truncate('Hi', 5) == 'Hi'

    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        assert StringUtil.truncate('Hello World', 5, suffix='…') == 'Hello…'

    def test_strip_html_tags(self):
        """Test HTML tag removal."""
        assert StringUtil.strip_html_tags('<p>Hello</p>') == 'Hello'
        assert StringUtil.strip_html_tags('<div><span>Test</span></div>') == 'Test'
        assert StringUtil.strip_html_tags('No tags') == 'No tags'

    def test_to_title_case(self):
        """Test title case conversion."""
        assert StringUtil.to_title_case('hello world') == 'Hello World'
        assert StringUtil.to_title_case('HELLO WORLD') == 'Hello World'

    @given(st.text(min_size=0, max_size=100))
    def test_is_blank_property(self, text: str):
        """Property test: is_blank should match Python's truthiness."""
        result = StringUtil.is_blank(text)
        expected = not text or text.isspace()
        assert result == expected
