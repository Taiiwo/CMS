# -*- coding: utf-8 -*-
#test on python 3.4 ,python of lower version  has different module organization.
from . import app

from flask import render_template

pages = {}


@app.route("/")
def index():
    return render_template("index.html", pages=pages)
