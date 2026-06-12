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

# Fetch 10 ZIM files at a time based on page number
def get_zim_files(page, language=None):
    offset = (page - 1) * 10
    connection = sqlite3.connect(config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Filter by language if user selects language
    if language:
        cursor.execute("SELECT * FROM library WHERE language = ? ORDER BY title ASC LIMIT 10 OFFSET ?", (language, offset))
    else:
        cursor.execute("SELECT * FROM library ORDER BY title ASC LIMIT 10 OFFSET ?", (offset,))
    rows = cursor.fetchall()
    connection.close()
    return rows

# Calculate total number of pages
def get_total_pages(language=None):
    connection = sqlite3.connect(config.DATABASE_PATH)
    cursor = connection.cursor()

    # Filter by language if user selects language
    if language:
        cursor.execute("SELECT COUNT(*) FROM library WHERE language = ?", (language,))
    else:
        cursor.execute("SELECT COUNT(*) FROM library")
    total = cursor.fetchone()[0]
    connection.close()
    return (total + 9) // 10

if __name__ == "__main__":
    init_db()
    print("Database initialized!")