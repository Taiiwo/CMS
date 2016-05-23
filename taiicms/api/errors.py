from . import api_logger
logger = api_logger.getChild("errors")

errors = [{
        "name": "unknown_error",
        "details": "We don't know what happened... but it was bad.",
        "status_code": 500
    },
    {
        "name": "json_invalid",
        "details": "The JSON recieved was invalid.",
        "status_code": 400
    },
    {
        "name": "data_required",
        "details": "A required field was missing.",
        "status_code": 400
    },
    {
        "name": "data_invalid",
        "details": "A field contained invalid data.",
        "status_code": 400
    },
    {
        "name": "username_taken",
        "details": "The username has been taken.",
        "status_code": 400
    },
    {
        "name": "login_invalid",
        "details": "The username and password did not match.",
        "status_code": 400
    },
    {
        "name": "login_required",
        "details": "The resource requested requires authentication.",
        "status_code": 400
    },
    {
        "name": "password_incorrect",
        "details": "Password given was incorrect.",
        "status_code": 400
    },
    {
        "name": "user_not_found",
        "details": "The specified user could not be found.",
        "status_code": 400
    },
]

error_names = {}

for err in errors:
    error_names[err["name"]] = err

has_warned = False
def add_error(name, details, status_code=500):
    global has_warned
    if not has_warned:
        api_logger.warn("`add_error(<error_data>)` is deprecated. Use `class <error>(taiicms.api.ApiError)` instead")
        has_warned = True

    error_names[name] = {
        "name": name,
        "details": details,
        "status_code": status_code
    }
