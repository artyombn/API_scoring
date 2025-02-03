import pytest

from scoring import get_interests, get_score, interests


@pytest.mark.parametrize(
    "arguments, score",
    [
        (
            {
                "store": 1,
                "phone": "79123456789",
                "email": "user@gmail.com",
                "birthday": "01.01.1996",
                "gender": 1,
                "first_name": "Alex",
                "last_name": "Stepnov",
            },
            5,
        ),
        (
            {
                "store": 1,
                "email": "user@gmail.com",
                "birthday": "01.01.1996",
                "gender": 1,
                "first_name": "Alex",
                "last_name": "Stepnov",
            },
            3.5,
        ),
        (
            {
                "store": 1,
                "phone": "79123456789",
                "birthday": "01.01.1996",
                "gender": 1,
                "first_name": "Alex",
                "last_name": "Stepnov",
            },
            3.5,
        ),
        (
            {
                "store": 1,
                "phone": "79123456789",
                "email": "user@gmail.com",
                "birthday": "01.01.1996",
                "first_name": "Alex",
                "last_name": "Stepnov",
            },
            3.5,
        ),
        (
            {
                "store": 1,
                "phone": "79123456789",
                "email": "user@gmail.com",
                "birthday": "01.01.1996",
                "gender": 1,
                "last_name": "Stepnov",
            },
            4.5,
        ),
        (
            {
                "store": 1,
                "birthday": "01.01.1996",
                "gender": 1,
                "first_name": "Alex",
                "last_name": "Stepnov",
            },
            2,
        ),
        (
            {
                "store": 1,
                "phone": "79123456789",
            },
            1.5,
        ),
        (
            {
                "store": 1,
                "email": "user@gmail.com",
            },
            1.5,
        ),
    ],
)
def test_get_score(arguments, score):
    if "phone" not in arguments.keys():
        arguments["phone"] = None
    if "email" not in arguments.keys():
        arguments["email"] = None
    assert get_score(**arguments) == score


def test_get_interests():
    data = interests
    assert isinstance(get_interests(None, None), list)
    assert len(get_interests(None, None)) == 2
    assert all(item in data for item in get_interests(None, None))
