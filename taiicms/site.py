# -*- coding: utf-8 -*-
#test on python 3.4 ,python of lower version  has different module organization.
from . import app

from flask import render_template

pages = {}

@app.route('/<path:path>')
def everything(path):
    return app.send_static_file(path)


@app.route("/")
def index():
    return render_template("index.html", pages=pages)
