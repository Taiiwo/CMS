from taiicms import app, config, save_config, plugins
from taiicms.api import make_error_response, make_success_response, user
from taiicms.api.errors import error_names, add_error

from flask import request
import json

add_error(
    "admin_required",
    "Admin privilidges are required to access this resource."
)

add_error(
    "config_invalid",
    "The config file sent was invalid."
)


def check_config(cfg):
    #TODO
    return True


@app.route("/api/plugin/admin/config", methods=["POST"])
def api_admin_config_get():
    user_data = user.authenticate()
    if user_data is None:
        return make_error_response("login_required")

    if not "is_admin" in user_data or not user_data["is_admin"]:
        return make_error_response("admin_required")

    return make_success_response({"config": config})

@app.route("/api/plugin/admin/config/save", methods=["POST"])
@app.route("/api/plugin/admin/config/update", methods=["POST"])
def api_admin_config_update():
    user_data = user.authenticate()
    if user_data is None:
        return make_error_response("login_required")

    if not user_data["is_admin"]:
        return make_error_response("admin_required")

    try:
        cfg = request.form["new_config"]
    except KeyError:
        return make_error_response("data_required", "new_config")

    try:
        cfg = json.loads(cfg)
    except KeyError:
        return make_error_response("json_invalid")

    if not check_config(cfg):
        return make_error_response("config_invalid")

    print(cfg)
    save_config(config_dict=cfg)

    return make_success_response()



def main(config):
    pass
