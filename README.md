# Library Catalog

A self-hosted offline digital library built with Flask and Python. Designed to run on a Raspberry Pi, it creates its own WiFi hotspot so users can access educational content from their phones or laptops without an internet connection.

---

## Motivation

Millions of people around the world lack reliable internet access, yet have a genuine desire to learn. This project aims to bridge that gap by providing a portable, offline-first library that any community can use.
This project is personal. I was born and raised in Haiti, a country where internet access remains limited and unreliable for much of the population. Haiti has an incredibly rich culture and a deep hunger for knowledge, yet access to educational resources remains out of reach for many. This library is built with that community in mind. It is designed to work in places like rural Haiti where connectivity is scarce but the desire to learn is not.
The interface supports the three languages most relevant to the communities this project serves: English, French, and Haitian Creole (Kreyòl). Content is sourced from open educational resources like Wikipedia, PhET Interactive Simulations, and Ekopedia, all available offline through the ZIM file format.

---

## Features

- Serves multiple ZIM files (Wikipedia, PhET simulations, Ekopedia, and more)
- Full-text search within ZIM files
- Multilingual interface (English, French, Haitian Creole)
- Auto-detects browser language
- Paginated library catalog with language filtering
- Runs as a WiFi hotspot on Raspberry Pi — no internet required
- Auto-starts on boot, no keyboard or monitor needed
- Mobile-friendly, works on any device with a browser

---

## Tech Stack

- **Python 3** — core language
- **Flask** — web framework
- **libzim** — reads and serves ZIM file content
- **SQLite** — stores library metadata
- **Gunicorn** — production WSGI server
- **NetworkManager** — manages WiFi hotspot on Raspberry Pi
- **HTML/CSS/Jinja2** — frontend templates

---

## Project Structure

```
Library-Catalog/
├── app.py              # Flask application entry point; registers routes and starts the server
├── config.py           # Stores application settings such as host, port, data folder path, and language defaults
├── database.py         # Manages SQLite connection, schema, and queries for ZIM file metadata
├── zim_manager.py      # Handles scanning the data/ folder, loading ZIM archives, and serving their content
├── library.db          # Auto-generated SQLite database (not tracked by Git)
├── data/               # Place ZIM files here (not tracked by Git)
├── templates/
│   ├── layout.html     # Base template with shared navigation, language selector, and page structure
│   ├── home.html       # Centralized library homepage listing all available ZIM files by language
│   └── search.html     # Displays search results from querying a ZIM file's index
├── static/
│   └── styles.css      # Haiti-themed stylesheet
└── translations/
    ├── fr.json         # French UI translations
    └── ht.json         # Haitian Creole UI translations
```

---

## Setup

### Requirements

- Python 3.11 or 3.12
- Raspberry Pi 4B

### Mac / Linux

```bash
# Clone the repository
git clone https://github.com/yourusername/Library-Catalog
cd Library-Catalog

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add ZIM files to the data/ folder
# then run the app
python app.py
```

Visit relevant IP in your browser.

### Windows

```powershell
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add ZIM files to the data/ folder
# then run the app
$env:ZIM_FILE="data/your_file.zim"
python app.py
```

Visit relevant IP in your browser.

---

## Adding ZIM Files

1. Download ZIM files from [https://library.kiwix.org](https://library.kiwix.org)
2. Name them using this convention: `Title_language.zim`
   - Example: `Chemistry_Wiki_en.zim`, `Ekopedia_fr.zim`
   - Supported language codes: `en`, `fr`, `ht`
3. Place them in the `data/` folder
4. Restart the app — the database updates automatically

---

## Raspberry Pi Deployment

### Prerequisites

```bash
sudo apt-get install network-manager -y
pip install flask libzim gunicorn
```

### Hotspot Setup

```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid YourNetworkName password YourPassword
sudo nmcli connection modify Hotspot autoconnect yes
```

### Auto-Start on Boot

Create `/etc/systemd/system/library.service`:

```
[Unit]
Description=Offline Library Catalog
After=network.target

[Service]
User=root
WorkingDirectory=/home/pi/Library-Catalog
Environment="PATH=/home/pi/Library-Catalog/venv/bin"
ExecStart=/home/pi/Library-Catalog/venv/bin/gunicorn -w 2 -b 0.0.0.0:80 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable library.service
sudo systemctl start library.service
```

Users connect to the WiFi network and visit the relevant IP in their browser.

### Stopping Auto-Start

```bash
sudo systemctl disable library.service
sudo systemctl stop library.service
```


