import datetime
import hashlib

import pytest

import api


@pytest.fixture
def context():
    return {}


@pytest.fixture
def headers():
    return {}


@pytest.fixture
def settings():
    return {}


def get_response(request, context, headers, settings):
    return api.method_handler({"body": request, "headers": headers}, context, settings)


def set_valid_auth(request):
    if request.get("login") == api.ADMIN_LOGIN:
        request["token"] = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode(
                "utf-8"
            )
        ).hexdigest()
    else:
        msg = (request.get("account", "") + request.get("login", "") + api.SALT).encode(
            "utf-8"
        )
        request["token"] = hashlib.sha512(msg).hexdigest()


def test_empty_request(context, headers, settings):
    _, code = get_response({}, context, headers, settings)
    assert code == api.INVALID_REQUEST


@pytest.mark.parametrize(
    "request_body, code, response",
    [
        (
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
            api.FORBIDDEN,
            "Forbidden",
        ),
        (
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "sdd",
                "arguments": {},
            },
            api.FORBIDDEN,
            "Forbidden",
        ),
        (
            {
                "account": "horns&hoofs",
                "login": "admin",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
            api.FORBIDDEN,
            "Forbidden",
        ),
    ],
)
def test_bad_auth(request_body, code, response, context, headers, settings):
    _, response_code = get_response(request_body, context, headers, settings)
    assert response_code == code
    assert _ == response


@pytest.mark.parametrize(
    "request_body, code, response",
    [
        (
            {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
            api.INVALID_REQUEST,
            "Invalid Request",
        ),
        (
            {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
            api.INVALID_REQUEST,
            "Invalid Request",
        ),
        (
            {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
            api.INVALID_REQUEST,
            "Invalid Request",
        ),
    ],
)
def test_invalid_method_request(
    request_body, code, response, context, headers, settings
):
    set_valid_auth(request_body)
    response_body, response_code = get_response(
        request_body, context, headers, settings
    )
    assert response_code == code
    assert response_body == response
    assert len(response_body) > 0


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.1890",
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "XXX",
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": 1,
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": "s",
            "last_name": 2,
        },
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ],
)
def test_invalid_score_request(arguments, context, headers, settings):
    request = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "online_score",
        "arguments": arguments,
    }
    set_valid_auth(request)
    response, code = get_response(request, context, headers, settings)
    assert (
        code == api.INVALID_REQUEST
    ), f"Expected {api.INVALID_REQUEST}, got {code} for arguments {arguments}"
    assert len(response) > 0


@pytest.mark.parametrize(
    "arguments",
    [
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": "a",
            "last_name": "b",
        },
    ],
)
def test_ok_score_request(arguments, context, headers, settings):
    request = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "online_score",
        "arguments": arguments,
    }
    set_valid_auth(request)
    response, code = get_response(request, context, headers, settings)
    assert code == api.OK, f"Expected {api.OK}, got {code} for arguments {arguments}"
    score = response.get("score")
    assert isinstance(score, (int, float)) and score >= 0
    assert sorted(context["has"]) == sorted(arguments.keys())


def test_ok_score_admin_request(context, headers, settings):
    arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
    request = {
        "account": "horns&hoofs",
        "login": "admin",
        "method": "online_score",
        "arguments": arguments,
    }
    set_valid_auth(request)
    response, code = get_response(request, context, headers, settings)
    assert code == api.OK, f"Expected {api.OK}, got {code} for arguments {arguments}"
    score = response.get("score")
    assert score == 42


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ],
)
def test_invalid_interests_request(arguments, context, headers, settings):
    request = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "clients_interests",
        "arguments": arguments,
    }
    set_valid_auth(request)
    response, code = get_response(request, context, headers, settings)
    assert (
        code == api.INVALID_REQUEST
    ), f"Expected {api.INVALID_REQUEST}, got {code} for arguments {arguments}"
    assert len(response) > 0


@pytest.mark.parametrize(
    "arguments",
    [
        {
            "client_ids": [1, 2, 3],
            "date": datetime.datetime.today().strftime("%d.%m.%Y"),
        },
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ],
)
def test_ok_interests_request(arguments, context, headers, settings):
    request = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "clients_interests",
        "arguments": arguments,
    }
    set_valid_auth(request)
    response, code = get_response(request, context, headers, settings)
    assert code == api.OK, f"Expected {api.OK}, got {code} for arguments {arguments}"
    assert len(arguments["client_ids"]) == len(response)
    assert all(
        v and isinstance(v, list) and all(isinstance(i, (bytes, str)) for i in v)
        for v in response.values()
    )
    assert context.get("nclients") == len(arguments["client_ids"])
