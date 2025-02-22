#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

from descriptor import Field
from scoring import get_interests, get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class CharField(Field):
    def validate(self, value):
        super().validate_char_field(value)
        return value


class ArgumentsField(Field):
    def validate(self, value):
        super().validate_arguments_field(value)
        return value


class EmailField(CharField):
    def validate(self, value):
        super().validate_email_field(value)
        return value


class PhoneField(Field):
    def validate(self, value):
        super().validate_phone_field(value)
        return value


class DateField(Field):
    def validate(self, value):
        super().validate_date_field(value)
        return value


class BirthDayField(DateField):
    def validate(self, value):
        super().validate_date_field(value)
        return value


class GenderField(Field):
    def validate(self, value):
        super().validate_gender_field(value)
        return value


class ClientIDsField(Field):
    def validate(self, value):
        super().validate_client_ids_field(value)
        return value


class ClientsInterestsRequest:
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest:
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def to_dict(self):
        return {
            attr: getattr(self, attr)
            for attr in self.__class__.__dict__
            if not attr.startswith("_")
        }


class MethodRequest:
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    def validate(self):
        if not self.login:
            raise ValueError(ERRORS[INVALID_REQUEST])
        if not self.token:
            raise ValueError(ERRORS[INVALID_REQUEST])
        if not self.method:
            raise ValueError(ERRORS[INVALID_REQUEST])
        if not self.arguments:
            raise ValueError(ERRORS[INVALID_REQUEST])

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + SALT).encode("utf-8")
        ).hexdigest()
    return digest == request.token


def parse_method_request(body):
    method_request = MethodRequest()
    method_request.login = body.get("login", "")
    method_request.token = body.get("token", "")
    method_request.account = body.get("account", "")
    method_request.method = body.get("method")
    method_request.arguments = body.get("arguments", {})
    return method_request


def handle_online_score(method_request, ctx, store):
    online_score_request = OnlineScoreRequest()

    try:
        online_score_request.phone = method_request.arguments.get("phone", "")
        online_score_request.email = method_request.arguments.get("email", "")
        online_score_request.birthday = method_request.arguments.get("birthday", "")
        online_score_request.gender = method_request.arguments.get("gender", "")
        online_score_request.first_name = method_request.arguments.get("first_name", "")
        online_score_request.last_name = method_request.arguments.get("last_name", "")

        arguments_list = []
        for argument in online_score_request.to_dict():
            if (
                online_score_request.to_dict()[argument] is None
                or online_score_request.to_dict()[argument] == ""
            ):
                continue
            arguments_list.append(argument)
        ctx["has"] = arguments_list[:-1]

        if not {"phone", "email"}.issubset(set(ctx["has"])):
            if not {"first_name", "last_name"}.issubset(set(ctx["has"])):
                if not {"gender", "birthday"}.issubset(set(ctx["has"])):
                    raise ValueError(ERRORS[INVALID_REQUEST])
    except TypeError as e:
        return str(e), INVALID_REQUEST
    except ValueError as e:
        return str(e), INVALID_REQUEST

    if method_request.is_admin:
        return {"score": 42}, OK

    score = get_score(
        store,
        online_score_request.phone,
        online_score_request.email,
        online_score_request.birthday,
        online_score_request.gender,
        online_score_request.first_name,
        online_score_request.last_name,
    )
    return {"score": score}, OK


def handle_clients_interests(method_request, ctx, store):
    clients_interests_request = ClientsInterestsRequest()

    try:
        clients_interests_request.client_ids = method_request.arguments.get(
            "client_ids"
        )
        clients_interests_request.date = method_request.arguments.get("date", None)

        ctx["nclients"] = len(clients_interests_request.client_ids)
    except TypeError as e:
        return str(e), INVALID_REQUEST
    except ValueError as e:
        return str(e), INVALID_REQUEST

    clients_interests_dict = {}
    for client_id in clients_interests_request.client_ids:
        if client_id in clients_interests_dict:
            continue
        clients_interests_dict[client_id] = get_interests(store, client_id)
    return clients_interests_dict, OK


def method_handler(request, ctx, store):
    response = {}
    code = OK

    body = request.get("body", {})
    method = body.get("method")

    try:
        method_request = parse_method_request(body)

        if not check_auth(method_request):
            return ERRORS[FORBIDDEN], FORBIDDEN

        method_request.validate()
    except ValueError as e:
        return str(e), INVALID_REQUEST

    if method == "online_score":
        return handle_online_score(method_request, ctx, store)

    if method == "clients_interests":
        return handle_clients_interests(method_request, ctx, store)

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
