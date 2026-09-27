# Expense Tracker — Web Version

Flask conversion of your original CustomTkinter desktop app. Same SQLite
schema and stats logic; the UI is now server-rendered HTML/CSS with
Chart.js instead of Tkinter/matplotlib.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## Deploy for free — Render.com

1. Push this folder to a GitHub repo.
2. Go to render.com → New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy. Render gives you a live `https://yourapp.onrender.com` URL.

## Deploy for free — Railway.app

1. Push to GitHub, then railway.app → New Project → Deploy from repo.
2. Railway auto-detects Flask. Set the start command to `gunicorn app:app` if it doesn't.
3. Deploy — you get a live URL automatically.

## Important note on the database

SQLite (`expenses.db`) is a local file. On Render/Railway's free tiers,
the filesystem is **not persistent** across deploys/restarts — your data
can be wiped. For a real production deployment, either:
- Use Render's/Railway's persistent disk add-on, or
- Switch to a hosted Postgres database (both platforms offer a free one)
  by swapping the `sqlite3` calls for `psycopg2`/`SQLAlchemy`.

For personal/small-scale use this is often fine as-is — just know a
restart may reset your expenses unless you add a persistent disk.
