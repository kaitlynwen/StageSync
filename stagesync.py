#!/usr/bin/env python

#-----------------------------------------------------------------------
# penny.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

import time
import flask
import database

#-----------------------------------------------------------------------

app = flask.Flask(__name__, template_folder='.')

#-----------------------------------------------------------------------

def get_ampm():
    if time.strftime('%p') == "AM":
        return 'morning'
    return 'afternoon'

def get_current_time():
    return time.asctime(time.localtime())

#-----------------------------------------------------------------------

@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():

    html_code = flask.render_template('index.html',
        ampm=get_ampm(),
        current_time=get_current_time())
    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/searchform', methods=['GET'])
def search_form():

    prev_author = flask.request.cookies.get('prev_author')
    if prev_author is None:
        prev_author = '(None)'

    html_code = flask.render_template('searchform.html',
        ampm=get_ampm(),
        current_time=get_current_time(),
        prev_author=prev_author)
    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/searchresults', methods=['GET'])
def search_results():

    author = flask.request.args.get('author')
    if author is None:
        author = ''
    author = author.strip()

    if author == '':
        prev_author = '(None)'
        books = []
    else:
        prev_author = author
        books = database.get_books(author) # Exception handling omitted
    html_code = flask.render_template('searchresults.html',
        ampm=get_ampm(),
        current_time=get_current_time(),
        author=prev_author,
        books=books)
    response = flask.make_response(html_code)
    response.set_cookie('prev_author', prev_author)
    return response
