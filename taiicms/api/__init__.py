from flask import make_response, jsonify
from flask.ext.cors import CORS

from .. import app, util, config, root_logger

api_logger = root_logger.getChild("api")

from .errors import error_names, add_error

# CORS(app)  # make app work across origins
util = util.Util(config["mongo"])


class ApiError(Exception):
    name = "api_error"
    details = "Something wrong happened with the data you send to the API."
    status_code = 200
    def __init__(self, data=None):
        self.data = data

    def to_dict(self):
        if self.data:
            return {
                "name": self.name,
                "details": self.details,
                "data": self.data,
                "status_code": self.status_code,
            }
        else:
            return {
                "name": self.name,
                "details": self.details,
                "status_code": self.status_code,
            }


class UnknownError(ApiError):
    name = "unknown_error"
    details = "We don't know what happened... but it was bad."
    status_code = 500


class JsonInvalid(ApiError):
    name = "json_invalid"
    details = "The JSON recieved was invalid."


class DataInvalid(ApiError):
    name = "data_invalid"
    details = "A field contained invalid data."
    status_code = 400

    def __init__(self, field):
        self.data = {"field": field}


class DataRequired(DataInvalid):
    name = "data_required"
    details = "A required field was missing."


@app.errorhandler(ApiError)
def api_exception_handler(e):
    error_data = e.to_dict()
    return jsonify({
        "success": False,
        "errors": [error_data]
    })


def make_success_response(extra={}):
    data_res = extra
    data_res["success"] = True
    res = make_response(jsonify(data_res), 200)
    return res


def make_error(error_name, extra_detail=None):
    if isinstance(error_name, list):
        res_errors = []
        for err in error_name:
            res_errors.append(errors.error_names[err])
    else:
        res_errors = [errors.error_names[error_name]]

    res = {
        "success": False,
        "errors": res_errors,
    }

    if extra_detail:
        res["extra"] = extra_detail

    return res



has_warned = False
def make_error_response(*args, **kwargs):
    global has_warned
    if not has_warned:
        api_logger.warn("`make_error_response(<error>)` is deprecated. Use `raise <error>()` instead")
        has_warned = True

    error_res = make_error(*args, **kwargs)
    res = make_response(jsonify(error_res), 200)
    return res


# has to go at the bottom to make sure functions are defined before we use them
from . import (
    user,
    errors,
)
