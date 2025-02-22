import datetime
import re


class Field:
    def __init__(self, required=True, nullable=False):
        self.required = required
        self.nullable = nullable
        self._value = None

    def __get__(self, obj, cls):
        return self._value

    def __set__(self, obj, val):
        self.validate(val)
        self._value = val

    def check_none(self, val):
        from api import ERRORS, INVALID_REQUEST

        if val is None or val == "":
            if not self.nullable:
                raise ValueError(ERRORS[INVALID_REQUEST])
            return True
        return False

    def validate_char_field(self, val):
        if self.check_none(val):
            return val
        if not isinstance(val, str):
            raise TypeError("Field must be a string")
        return val

    def validate_arguments_field(self, val):
        if self.check_none(val):
            return val
        if not isinstance(val, dict):
            raise TypeError("Field must be a dict")
        return val

    def validate_email_field(self, val):
        EMAIL_PATTERN = re.compile(
            r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
        )

        if self.check_none(val):
            return val
        if isinstance(val, str):
            if not EMAIL_PATTERN.match(val):
                raise ValueError("Field must be an email format")
            return val
        raise TypeError("Field must be a string")

    def validate_phone_field(self, val):
        if self.check_none(val):
            return val
        if not isinstance(val, (int, str)):
            raise TypeError("Field must be int or str")

        str_value = str(val)
        if len(str_value) != 11:
            raise ValueError("Field must have 11 figures")
        if str_value[0] != "7":
            raise ValueError("Field must start from 7")
        return val

    def validate_date_field(self, val):
        if self.check_none(val):
            return val

        if not isinstance(val, str):
            raise TypeError("Date format must be str")

        try:
            value_date = datetime.datetime.strptime(val, "%d.%m.%Y")
        except ValueError as exc:
            raise ValueError("Time data does not match format '%d.%m.%Y'") from exc

        date_now = datetime.datetime.now()
        difference = date_now - value_date
        if difference.days > 25570:
            raise ValueError("Birthday must be < 70 years")

        return val

    def validate_gender_field(self, val):
        if self.check_none(val):
            return val
        if not isinstance(val, int):
            raise TypeError("Field must be int")
        if val not in [0, 1, 2]:
            raise ValueError("Value must be 0 or 1 or 2")
        return val

    def validate_client_ids_field(self, val):
        if not isinstance(val, list):
            raise TypeError("Field must be a list")
        if len(val) == 0:
            raise ValueError("List cannot be empty")
        if not all(isinstance(x, int) for x in val):
            raise TypeError("All list items must be int")
        return val
