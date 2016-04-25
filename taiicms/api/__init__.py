from flask import make_response, jsonify
from flask.ext.cors import CORS

from .errors import error_names
from .. import app, util, config

CORS(app)  # make app work across origins
util = util.Util(config["mongo"])


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


def make_error_response(*args, **kwargs):
    error_res = make_error(*args, **kwargs)
    res = make_response(jsonify(error_res), 200)
    return res


# has to go at the bottom to make sure functions are defined before we use them
from . import (
    user,
    errors,
)
