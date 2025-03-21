import flask

# Initialize Flask app
app = flask.Flask(
    "stagesync",
    template_folder="templates",  # Folder for HTML files
    static_folder="static",  # Folder for CSS, JS, and images
)