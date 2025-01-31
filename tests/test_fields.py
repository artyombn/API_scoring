import pytest
from contextlib import nullcontext as does_not_raise

from descriptor import Field

@pytest.mark.parametrize(
    "nullable, val, res, expectation",
    [
        (True, None, True, does_not_raise()),
        (False, None, False, pytest.raises(ValueError, match="^Field cannot be null$")),
        (False, "val", False, does_not_raise()),
    ]
)
def test_check_none(nullable, val, res, expectation):
    field = Field(nullable=nullable)
    with expectation:
        assert field.check_none(val) is res

@pytest.mark.parametrize(
    "val, res, expectation",
    [
        (None, None, does_not_raise()),
        ("Test", "Test", does_not_raise()),
        ("", "", does_not_raise()),
        (123, "123", pytest.raises(TypeError, match="^Field must be a string$")),
        ([1, 2, 3], "[1, 2, 3]", pytest.raises(TypeError, match="^Field must be a string$")),
    ]
)
def test_validate_char_field(val, res, expectation):
    field = Field(nullable=True)

    with expectation:
        assert field.validate_char_field(val) == res

@pytest.mark.parametrize(
    "val, res, expectation",
    [
        (None, None, does_not_raise()),
        ("test@gmail.com", "test@gmail.com", does_not_raise()),
        ("test@", "test@", pytest.raises(ValueError, match="^Field must be an email format$")),
        (123, "123", pytest.raises(TypeError, match="^Field must be a string$")),
        ("test@gmail.", "test@gmail.", pytest.raises(ValueError, match="^Field must be an email format$")),
        ("user@com", "user@com", pytest.raises(ValueError, match="^Field must be an email format$")),
    ]
)
def test_validate_email_field(val, res, expectation):
    field = Field(nullable=True)

    with expectation:
        assert field.validate_email_field(val) == res
