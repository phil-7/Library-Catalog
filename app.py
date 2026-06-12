# app.py         - Flask application entry point; registers routes and starts the server
from flask import Flask, request, render_template

from database import init_db, get_zim_files, get_total_pages
from zim_manager import populate_database
import config

#Initiate app
app = Flask(__name__)

# Creates database if it doesn't exist
init_db()

# Scans data/ and fills the database
populate_database()


# Main Page for Library Catalog
@app.route("/")
def index():
    
    page = int(request.args.get("page", 1))

    zim_files = get_zim_files(page)
    total_pages = get_total_pages()

    return render_template("home.html", page=page, total_pages=total_pages, zim_files=zim_files)

@app.route("/search")
def search():
    return "search page coming soon"

@app.route("/reader")
def reader():
    return "search page coming soon"


if __name__ == "__main__":
    app.run(debug=True)