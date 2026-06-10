from flask import Flask, Response, abort
from libzim.reader import Archive

zim = Archive("data/phet_ht_all_2026-05.zim")   # Load once at startup

app = Flask(__name__)

def get_entry(path):
    try:
        return zim.get_entry_by_path(path)
    except KeyError:
        return None

@app.route("/")
def index():
    # Redirect to the ZIM main page
    main_path = zim.main_entry.get_item().path
    return f'<a href="/zim/{main_path}">Open ZIM main page</a>'

@app.route("/zim/<path:entry_path>")
def serve_zim(entry_path):
    try:
        entry = zim.get_entry_by_path(entry_path)
    except KeyError:
        abort(404)

    item = entry.get_item()

    # Debug: show what we CAN inspect
    print("DEBUG → Entry path:", entry.path)
    print("DEBUG → Entry title:", entry.title)
    print("DEBUG → Item size:", item.size)
    print("DEBUG → Item mimetype:", item.mimetype)

    # Serve content
    data = item.content
    mimetype = item.mimetype

    return Response(data, mimetype=mimetype)





if __name__ == "__main__":
    app.run(debug=True)
