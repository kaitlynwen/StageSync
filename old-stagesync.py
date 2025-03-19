#!/usr/bin/env python

#-----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
#-----------------------------------------------------------------------

import os
import time
import flask
import dotenv
import auth
# import database

from top import app

#-----------------------------------------------------------------------

dotenv.load_dotenv()
app.secret_key = os.environ['APP_SECRET_KEY'] # Make sure to add .env

#-----------------------------------------------------------------------

def get_current_time():
    return time.asctime(time.localtime())

#-----------------------------------------------------------------------

@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    # code only used as filler
    user_info = auth.authenticate()
    # print(user_info)
    username = user_info['user']
    return username

#-----------------------------------------------------------------------

@app.route('/updateavailability', methods=['GET'])
def update_availability():
    user_info = auth.authenticate()
    # print(user_info)
    username = user_info['user']
    return username

#-----------------------------------------------------------------------

@app.route('/generateschedule', methods=['GET'])
def generate_schedule():
    # should be visible only to admins
    user_info = auth.authenticate()
    # print(user_info)
    username = user_info['user']
    return username