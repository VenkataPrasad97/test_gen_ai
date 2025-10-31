# backend/tests/test_utils.py
import pytest
from backend.utils import add_numbers, get_greeting

def test_add_numbers_positive():
    """Tests adding two positive numbers."""
    assert add_numbers(5, 10) == 15

def test_add_numbers_negative():
    """Tests adding two negative numbers."""
    assert add_numbers(-1, -5) == -6

def test_add_numbers_type_error():
    """Tests that non-numbers raise a TypeError."""
    with pytest.raises(TypeError):
        add_numbers("a", "b")

def test_get_greeting_with_name():
    """Tests the greeting with a name provided."""
    assert get_greeting("Alice") == "Hello, Alice!"

def test_get_greeting_no_name():
    """Tests the greeting with no name (empty string)."""
    assert get_greeting("") == "Hello, stranger!"