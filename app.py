# app.py
from flask import Flask, Response, request, render_template_string, abort
from libzim.reader import Archive
from libzim.search import Query, Searcher
from libzim.suggestion import SuggestionSearcher
import mimetypes
import os

app = Flask(__name__)

# --- Load ZIM file ---
ZIM_PATH = os.environ.get("ZIM_FILE", "data/phet_ht_all_2026-05.zim")
zim = Archive(ZIM_PATH)

# -------------------------------------------------------
# HOME: redirect to ZIM's main entry
# -------------------------------------------------------
@app.route("/")
def index():
    main_path = zim.main_entry.get_item().path
    return app.redirect(f"/zim/{main_path}")


# -------------------------------------------------------
# SEARCH endpoint (uses libzim full-text index)
# -------------------------------------------------------
SEARCH_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Search</title>
<style>
  body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
  input[type=text] { width: 70%; padding: 8px; font-size: 16px; }
  button { padding: 8px 16px; font-size: 16px; }
  ul { list-style: none; padding: 0; }
  li { margin: 10px 0; }
  a { font-size: 18px; color: #1a0dab; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .count { color: #666; font-size: 14px; margin-bottom: 16px; }
</style>
</head>
<body>
<h2>🔍 ZIM Search</h2>
<form action="/search" method="get">
  <input type="text" name="q" value="{{ query }}" placeholder="Search...">
  <button type="submit">Search</button>
</form>
{% if query %}
  <p class="count">~{{ count }} results for "<b>{{ query }}</b>"</p>
  <ul>
  {% for r in results %}
    <li><a href="/zim/{{ r.path }}">{{ r.title }}</a></li>
  {% endfor %}
  </ul>
  {% if count == 0 %}
    <p>No results found. Try a different search term.</p>
  {% endif %}
{% endif %}
<p><a href="/">← Back to main page</a></p>
</body>
</html>
"""

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    results = []
    count = 0
    if q:
        try:
            searcher = Searcher(zim)
            query = Query().set_query(q)
            search = searcher.search(query)
            count = search.getEstimatedMatches()
            results = list(search.getResults(0, 25))  # first 25 results
        except Exception as e:
            # ZIM may not have a full-text index (older files)
            pass
    return render_template_string(SEARCH_TEMPLATE, query=q, results=results, count=count)


# -------------------------------------------------------
# SERVE ZIM content (articles, images, JS, CSS, etc.)
# -------------------------------------------------------
@app.route("/zim/<path:zim_path>")
def serve_zim(zim_path):
    try:
        entry = zim.get_entry_by_path(zim_path)
    except KeyError:
        # Try with common fallback paths
        for candidate in [zim_path + "/index.htm", zim_path + "/index.html"]:
            try:
                entry = zim.get_entry_by_path(candidate)
                break
            except KeyError:
                pass
        else:
            abort(404)

    # Follow redirects
    while entry.is_redirect:
        entry = entry.get_redirect_entry()

    item = entry.get_item()
    content = bytes(item.content)
    mimetype = item.mimetype

    # Fallback mimetype detection
    if not mimetype or mimetype == "text/html":
        guessed, _ = mimetypes.guess_type(zim_path)
        if guessed:
            mimetype = guessed

    # CRITICAL for PhET and JS-heavy ZIMs:
    # Inject a <base> tag so relative URLs resolve correctly,
    # and add a search bar to HTML pages
    if "text/html" in mimetype:
        try:
            html = content.decode("utf-8", errors="replace")
            base_tag = f'<base href="/zim/{"/".join(zim_path.split("/")[:-1])}/">'
            search_bar = (
                '<div style="position:fixed;top:0;right:0;background:#fff;'
                'border:1px solid #ccc;padding:6px 10px;z-index:99999;font-family:sans-serif;font-size:13px;">'
                '<a href="/search" style="text-decoration:none">🔍 Search</a> | '
                '<a href="/" style="text-decoration:none">🏠 Home</a>'
                '</div>'
            )
            # Inject base tag after <head>
            if "<head>" in html:
                html = html.replace("<head>", f"<head>{base_tag}", 1)
            elif "<HEAD>" in html:
                html = html.replace("<HEAD>", f"<HEAD>{base_tag}", 1)
            # Add search bar
            if "</body>" in html:
                html = html.replace("</body>", f"{search_bar}</body>", 1)
            elif "</BODY>" in html:
                html = html.replace("</BODY>", f"{search_bar}</BODY>", 1)
            else:
                html = html + search_bar
            content = html.encode("utf-8")
        except Exception:
            pass  # serve raw on any encoding issue

    response = Response(content, mimetype=mimetype)
    # Allow JS modules and cross-origin fetches (PhET needs this)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response


if __name__ == "__main__":
    print(f"Serving: {ZIM_PATH}")
    print(f"Main entry: {zim.main_entry.get_item().path}")
    app.run(debug=True, port=5000)