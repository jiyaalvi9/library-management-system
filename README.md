# Library Management System

A simple full-stack app to manage books, members and loans.
Built by [jiyaalvi9](https://github.com/jiyaalvi9).

## Architecture

```
Browser (frontend/: HTML + CSS + JS)
        |  fetch() JSON
        v
Flask REST API (backend/app.py)
        |  sqlite3
        v
SQLite database (backend/library.db, created automatically)
```

## Project structure

```
library-management-system/
├── backend/    Flask API + SQLite
├── frontend/   Web UI (served by Flask)
├── docs/       Documentation
├── README.md
└── .gitignore
```

## Features

- Add / delete books (with number of copies)
- Add / delete members
- Issue a book (14-day loan), return a book, overdue highlighting
- Stock tracking: available copies update automatically

## Run it

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/books` | List / add books |
| DELETE | `/api/books/<id>` | Delete a book |
| GET/POST | `/api/members` | List / add members |
| DELETE | `/api/members/<id>` | Delete a member |
| GET/POST | `/api/loans` | List / issue loans |
| POST | `/api/loans/<id>/return` | Return a book |
