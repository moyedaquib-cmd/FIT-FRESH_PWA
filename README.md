# Fit & Fresh — Setup & Run Guide

Fit & Fresh is a role-based fitness tracking Progressive Web App (PWA) built with Python, Flask, and SQLite3. It allows gym-goers to log workouts and calories and discover trainer-published exercises, meal plans and routines, while personal trainers can upload and manage content that all users can review, rate and favourite.

---

## Requirements

- **Python 3.10 or later**
- **pip** (Python package manager)
- A modern web browser (Google Chrome recommended for full PWA/offline support)

---

## Setup Instructions

### 1. Install the required libraries

From inside the project folder, run:

```bash
pip install -r requirements.txt
```

This installs Flask, Werkzeug, and pytz.

### 2. Initialise the database (first run only)

The application uses a SQLite database (`instance/app.db`). If the database is not already included, create it by running Python and calling the init function:

```bash
python
```

Then, inside the Python prompt:

```python
from App import app
from DB_Models import init_db
with app.app_context():
    init_db()
exit()
```

*(A pre-built database with sample data may already be included in the `instance/` folder, in which case this step can be skipped.)*

### 3. Start the application

```bash
python App.py
```

The terminal will show that the server is running, typically at:

```
http://127.0.0.1:5000
```

### 4. Open the app

Open the address above in your web browser.

---

## Using the App

1. **Register** an account — choose either the **Gym Goer** or **Personal Trainer** role.
2. **Log in** with your new account.
3. **Gym Goers** can log workouts and calories, browse content, and favourite/review items.
4. **Personal Trainers** can additionally upload exercises, meal plans and routines via the **Add Content** page.

### Installing as a PWA (optional)

In Chrome, an **install icon** appears in the address bar. Clicking it installs Fit & Fresh as a standalone app. Once visited, pages are cached and remain viewable offline.

---

## Project Structure

```
FIT&FRESH_PWA/
├── App.py                 Main Flask application (routes and logic)
├── DB_Models.py           Database connection and table creation
├── requirements.txt       Python dependencies
├── instance/
│   └── app.db             SQLite database
├── templates/             HTML pages (Jinja2 templates)
└── static/
    ├── style.css          Application styles
    ├── service-worker.js  PWA offline service worker
    ├── manifest.json      PWA manifest
    └── images/            Icons and images
```

---

## Notes

- All passwords are securely hashed (scrypt) before storage; no plaintext passwords are kept.
- The app runs entirely locally — no internet connection or external services are required (aside from an icon CDN for display).
- For the best experience, and to test the offline/installable PWA features, use Google Chrome.