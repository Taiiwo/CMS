if __name__ != "__main__":
    raise ImportError("This is a testing module. Do not import.")

import requests
import json

login = requests.post(
    "http://localhost:5000/api/1/login",
    {
        "username": "Test",
        "password": "password"
    }
)

login_data = json.loads(login.text)

if not login_data["success"]:
    print("Could not log in.")
    raise SystemExit()

session_token = login_data["session"]
user_id = login_data["user_id"]

s1_res = requests.post(
    "http://localhost:5000/api/plugin/payment/step_one",
    {
        "session": session_token,
        "user_id": user_id
    }
)
s1_data = json.loads(s1_res.text)

if not s1_data["success"]:
    print("Could not get form URL.")
    raise SystemExit()

post_url = s1_data["url"]

test_data = {
    "billing-cc-number": "4111111111111111",
    "billing-cc-exp": "10/25"
}

s2_res = requests.post(post_url, test_data)
print(s2_res.text)
