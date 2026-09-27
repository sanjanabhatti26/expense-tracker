# Expense Tracker

A web app to track daily expenses — add, edit, delete entries, and see
spending broken down by category and month with charts.

Originally built as a desktop app (Python + CustomTkinter), later
converted into a Flask web app so it could be deployed and used from
any browser.

## Features

- Dashboard with total spending, this month's spending, and top category
- Add / edit / delete expenses
- All expenses table
- Category and monthly spending charts (bar, pie, line)

## Tech Stack

Python, Flask, SQLAlchemy, SQLite (dev) / PostgreSQL (production),
Chart.js

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## Deployment

Deployed on Render, with a PostgreSQL database attached through the
`DATABASE_URL` environment variable. Locally, it falls back to SQLite
automatically if `DATABASE_URL` isn't set.


Start command: `gunicorn app:app`

