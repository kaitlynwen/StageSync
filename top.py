#!/usr/bin/env python

# ----------------------------------------------------------------------
# top.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
# ----------------------------------------------------------------------

import os
import flask
import dotenv
from flask_wtf.csrf import CSRFProtect

# Initialize Flask app
app = flask.Flask(
    "stagesync",
    template_folder="templates",  # Folder for HTML files
    static_folder="static",  # Folder for CSS, JS, and images
    static_url_path='/static',
)

# load environmental variables
dotenv.load_dotenv()

app.secret_key = os.environ['APP_SECRET_KEY']

# Temp set debug to true
app.debug = True

csrf = CSRFProtect(app)