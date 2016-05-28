import logging
import os

from flask import Flask
from flask_socketio import SocketIO
app = Flask(__name__)
socket = SocketIO(app)

root_logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(ch)

# import config in a special way to make more intuitive to use
from .config import config, save_config, merge_dicts


from . import (
    api,
    plugins,
    schedule,
    site,
    socket_handlers,
    util,
)
