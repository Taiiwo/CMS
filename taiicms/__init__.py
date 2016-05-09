from flask import Flask
from flask_socketio import SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# import config in a special way to make more intuitive to use
from .config import config, save_config, merge_dicts

from . import (
    api,
    plugins,
    site
)
