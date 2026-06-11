# zim_manager.py - Handles scanning the data/ folder, loading ZIM archives, and serving their content
import config
import glob
import os
import sqlite3

# Scans data/ folder and returns a list of .zim filenames
def scan_zim_files():
    filename = glob.glob(os.path.join(config.DATA_FOLDER, "*.zim"))
    return filename
    
# Extracts title and language code from ZIM filename
def parse_zim_filename(filename):
    name = filename.removesuffix('.zim').removeprefix(config.DATA_FOLDER)
    parts = name.split("_")
    language = parts[-1] # grabs last item of the list
    title = " ".join(parts[:-1]) # joins remaining items of list, sperated by a space
    return title, language

# Uses scan and parse functions to insert records into database
def populate_database():

    # Open database
    connection = sqlite3.connect(config.DATABASE_PATH)
    cursor = connection.cursor()

    # Houses list of files in data/
    files = scan_zim_files()

    # For each file in files, parse the filename
    for file in files:
        title, language = parse_zim_filename(file)

        # Insert into database using title, language, file (path), filename
        cursor.execute("INSERT OR IGNORE INTO library (filename, title, language, path) VALUES (?, ?, ?, ?)", (file.removeprefix(config.DATA_FOLDER), title, language, file))
    connection.commit()
    connection.close()

if __name__ == "__main__":
    populate_database()
    print("ZIM files scanned and database populated!")