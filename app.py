# app.py         - Flask application entry point; registers routes and starts the server
from flask import Flask, request, render_template, Response, abort, redirect

from libzim.reader import Archive
from libzim.search import Query, Searcher

from database import init_db, get_zim_files, get_total_pages
from zim_manager import populate_database

import mimetypes

import config


# Initiate app
app = Flask(__name__)

# Creates database if it doesn't exist
init_db()

# Scans data/ and fills the database
populate_database()


# Main Page for Library Catalog
@app.route("/")
def index():
    
    page = int(request.args.get("page", 1))
    language = request.args.get("language", None)

    zim_files = get_zim_files(page, language)
    total_pages = get_total_pages(language)

    return render_template("home.html", page=page, total_pages=total_pages, zim_files=zim_files, language=language)


@app.route("/reader/<path:zim_path>")
def reader(zim_path):

    # Split URL into ZIM file path and article path inside the ZIM
    parts = zim_path.split(".zim")
    zim_file = Archive(parts[0] + ".zim")
    article_path = parts[1].lstrip("/").lstrip("\\")

    # If no article path, redirect to ZIM's main entry page
    if not article_path:
        main_path = zim_file.main_entry.get_item().path
        return redirect(f"/reader/{parts[0]}.zim/{main_path}")

    # Get the entry from the ZIM file, return 404 if not found
    try:
        entry = zim_file.get_entry_by_path(article_path)
    except KeyError:
        abort(404)

    # Follow any redirects within the ZIM until we reach actual content
    while entry.is_redirect:
        entry = entry.get_redirect_entry()

    # Extract raw content and mimetype from the entry
    item = entry.get_item()
    content = bytes(item.content)
    mimetype = item.mimetype

    # Fallback mimetype detection if ZIM doesn't provide one
    if not mimetype or mimetype == "text/html":
        guessed, _ = mimetypes.guess_type(article_path)
        if guessed:
            mimetype = guessed

    # Inject base tag and search bar into HTML pages
    if "text/html" in mimetype:
        try:
            html = content.decode("utf-8", errors="replace")

            # Inject base tag so relative URLs resolve correctly
            article_dir = "/".join(article_path.split("/")[:-1])
            base_tag = f'<base href="/reader/{parts[0]}.zim/{article_dir}/">'
            if "<head>" in html:
                html = html.replace("<head>", f"<head>{base_tag}", 1)
            elif "<HEAD>" in html:
                html = html.replace("<HEAD>", f"<HEAD>{base_tag}", 1)

            # Inject floating search bar and home button overlay
            search_bar = (
                '<div style="position:fixed;top:0;right:0;background:#fff;'
                'border:1px solid #ccc;padding:6px 10px;z-index:99999;font-family:sans-serif;font-size:13px;">'
                f'<a href="/search?zim={parts[0]}.zim" style="text-decoration:none">🔍 Search</a> | '
                '<a href="/" style="text-decoration:none">🏠 Home</a>'
                '</div>'
            )
            if "</body>" in html:
                html = html.replace("</body>", f"{search_bar}</body>", 1)
            elif "</BODY>" in html:
                html = html.replace("</BODY>", f"{search_bar}</BODY>", 1)
            else:
                html = html + search_bar

            content = html.encode("utf-8")
        except Exception:
            pass

    # Build and return response with CORS headers for PhET/JS-heavy ZIMs
    response = Response(content, mimetype=mimetype)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response

@app.route("/search")
def search():

    # Get search query and ZIM file path from URL
    q = request.args.get("q", "").strip()
    zim_path = request.args.get("zim", "")

    results = []
    count = 0

    # Only search if both a query and ZIM file are provided
    if q and zim_path:
        try:
            # Open the ZIM file and run the search
            zim = Archive(zim_path)
            searcher = Searcher(zim)
            query = Query().set_query(q)
            search_obj = searcher.search(query)
            count = search_obj.getEstimatedMatches()

            # Build results list from search hits
            for result in search_obj.getResults(0, 25):
                try:
                    entry = zim.get_entry_by_path(result)
                    results.append({
                        "path": result,
                        "title": entry.title
                    })
                except KeyError:
                    results.append({
                        "path": result,
                        "title": result
                    })
        except Exception as e:
            print(f"Search error: {e}")

    return render_template("search.html", query=q, results=results, count=count, zim_path=zim_path)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
    
    # on Mac, Run flask run --host=0.0.0.0 --port=5001 to log on with phone