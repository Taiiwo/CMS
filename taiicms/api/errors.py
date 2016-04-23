error_codes = {
    -1: {
        "name": "unknown_error",
        "details": "We don't know what happened... but it was bad.",
        "status_code": 500
    },
    1: {
        "name": "json_invalid",
        "details": "The JSON recieved was invalid.",
        "status_code": 400
    },
    2: {
        "name": "data_required",
        "details": "A required field was missing.",
        "status_code": 400
    },
    3: {
        "name": "data_invalid",
        "details": "A field contained invalid data.",
        "status_code": 400
    },
    4: {
        "name": "username_taken",
        "details": "The username request has been taken.",
        "status_code": 400
    },
    5: {
        "name": "login_invalid",
        "details": "The username and password did not match.",
        "status_code": 400
    },
    6: {
        "name": "login_required",
        "details": "The resource requested requires authentication.",
        "status_code": 400
    },
    7: {
        "name": "password_incorrect",
        "details": "A field contained invalid data.",
        "status_code": 400
    },
    8: {
        "name": "user_not_found",
        "details": "The specified user could not be found.",
        "status_code": 400
    },
}

error_names = {}

for err in error_codes.keys():
    error_codes[err]["id"] = err

for err in error_codes.values():
    error_names[err["name"]] = err
