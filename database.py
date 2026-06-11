# database.py    - Manages SQLite connection, schema, and queries for ZIM file metadata
import config
import sqlite3

# Create a database if it does not exist yet
def init_db():
    connection = sqlite3.connect(config.DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS library(" \
    "id INTEGER PRIMARY KEY AUTOINCREMENT," \
    "filename TEXT UNIQUE," \
    "title TEXT," \
    "language TEXT," \
    "path TEXT" \
    ")")
    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized!")