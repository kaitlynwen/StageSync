#!/usr/bin/env python

#-----------------------------------------------------------------------
# stagesync.py
# Author: Kaitlyn Wen, Michael Igbinoba, Timothy Sim
#-----------------------------------------------------------------------

from flask import render_template
import flask
import os
import dotenv
# import auth

#-----------------------------------------------------------------------

# Load environment variables
dotenv.load_dotenv()

# Initialize Flask app
app = flask.Flask(
    'stagesync', 
    template_folder='templates',  # Folder for HTML files
    static_folder='static'  # Folder for CSS, JS, and images
)

# Secret key setup (set up in .env)
app.secret_key = os.environ.get('APP_SECRET_KEY', 'your_default_secret_key')  # Make sure .env has the APP_SECRET_KEY

#-----------------------------------------------------------------------

# Routes
@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    # Temporarily bypass authentication and default to admin
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    
    # Check if the user is an admin
    if user_info.get('is_admin', False):
        # Render home-admin.html if the user is an admin
        return render_template('home-admin.html', user=user_info)
    else:
        # Render home.html for regular users
        return render_template('home.html', user=user_info)

@app.route('/settings', methods=['GET'])
def settings():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    return render_template('settings.html', user=user_info)

@app.route('/update-availability', methods=['GET'])
def update():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    return render_template('update.html', user=user_info)

@app.route('/view-schedule', methods=['GET'])
def view():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    return render_template('view.html', user=user_info)

@app.route('/upload-data', methods=['GET'])
def upload():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
        # Check if the user is an admin
    if user_info.get('is_admin', False):
        return render_template('upload.html', user=user_info)
    else:
        return None

@app.route('/generate-schedule', methods=['GET'])
def generate():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    if user_info.get('is_admin', False):
        return render_template('generate.html', user=user_info)
    else:
        return None

@app.route('/publish-schedule', methods=['GET'])
def publish():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    if user_info.get('is_admin', False):
        return render_template('publish.html', user=user_info)
    else:
        return None
    
@app.route('/manage-members', methods=['GET'])
def manage_admins():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    if user_info.get('is_admin', False):
        return render_template('manage-members.html', user=user_info)
    else:
        return None

@app.route('/manage-admins', methods=['GET'])
def manage_admins():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    if user_info.get('is_admin', False):
        return render_template('manage-admins.html', user=user_info)
    else:
        return None
    
@app.route('/manage-groups', methods=['GET'])
def manage_groups():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    if user_info.get('is_admin', False):
        return render_template('groups.html', user=user_info)
    else:
        return None
    
@app.route('/availability', methods=['GET'])
def availability():
    user_info = {
        'user': 'Admin User',
        'is_admin': True
    }
    if user_info.get('is_admin', False):
        return render_template('availability.html', user=user_info)
    else:
        return None

#-----------------------------------------------------------------------

# If the file is being executed directly, run the app
if __name__ == '__main__':
    app.run(debug=True)
