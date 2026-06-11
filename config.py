# config.py      - Stores application settings such as host, port, data folder path, and language defaults
import os

DATA_FOLDER = os.path.join("data", "")
FLASK_PORT= 5000
FLASK_HOST = "0.0.0.0"
LANGUAGES = {
    "en" : "English",
    "ht" : "Haitian Creole",
    "fr" : "French"
}
DATABASE_PATH = "library.db"