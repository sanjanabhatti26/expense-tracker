import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # replace with a real secret in production

# =========================================================
# DATABASE
# =========================================================



_raw_url = os.environ.get("DATABASE_URL", "sqlite:///expenses.db")

# Render's Postgres URLs start with "postgres://", but SQLAlchemy/psycopg2
# require "postgresql://" — swap it if needed.
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(_raw_url, pool_pre_ping=True)
IS_POSTGRES = engine.dialect.name == "postgresql"

CATEGORIES = [
    "Home",
    "Food",
    "Rent",
    "Party",
    "Shopping",
    "Travel",
    "Other",
]

CATEGORY_COLORS = {
    "Home": "#5B8DEF",
    "Food": "#FF9F43",
    "Rent": "#EA5455",
    "Party": "#A66CFF",
    "Shopping": "#C8A2C8",
    "Travel": "#00CFE8",
    "Other": "#7C7C8A",
}


def ensure_database():
    # Postgres and SQLite spell "auto-incrementing integer primary key"
    id_column = "id SERIAL PRIMARY KEY" if IS_POSTGRES else "id INTEGER PRIMARY KEY AUTOINCREMENT"

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS expenses (
                {id_column},
                expense_name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """))


def load_expenses():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, expense_name, amount, category, date
            FROM expenses
            ORDER BY id
        """)).mappings().all()
    return [dict(row) for row in rows]


def get_expense(expense_id):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM expenses WHERE id = :id"),
            {"id": expense_id},
        ).mappings().first()
    return dict(row) if row else None


def save_expense(expense):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO expenses (expense_name, amount, category, date)
                VALUES (:expense_name, :amount, :category, :date)
            """),
            expense,
        )


def delete_expense(expense_id):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM expenses WHERE id = :id"),
            {"id": expense_id},
        )


def update_expense(expense_id, name, amount, category, date):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE expenses
                SET expense_name = :name, amount = :amount, category = :category, date = :date
                WHERE id = :id
            """),
            {"name": name, "amount": amount, "category": category, "date": date, "id": expense_id},
        )


# =========================================================
# STATISTICS
# =========================================================

def compute_stats(expenses):
    total = 0.0
    category_totals = {}
    monthly_totals = {}

    for e in expenses:
        amount = float(e["amount"])
        category = e["category"].strip()
        date = e["date"]

        total += amount
        category_totals[category] = category_totals.get(category, 0) + amount

        month = date[:7]
        monthly_totals[month] = monthly_totals.get(month, 0) + amount

    top_category = max(category_totals, key=category_totals.get) if category_totals else "—"
    this_month = datetime.now().strftime("%Y-%m")
    month_spend = monthly_totals.get(this_month, 0)

    return {
        "total": total,
        "category_totals": category_totals,
        "monthly_totals": monthly_totals,
        "top_category": top_category,
        "month_spend": month_spend,
        "count": len(expenses),
    }


def validate_expense_form(name, amount_raw, date):
    """Returns (is_valid, error_message, amount_as_float)."""
    if not name:
        return False, "Please enter an expense name.", None

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return False, "Please enter a valid positive amount.", None

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False, "Please use YYYY-MM-DD format for the date.", None

    return True, None, amount


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def dashboard():
    expenses = load_expenses()
    stats = compute_stats(expenses)
    recent = list(reversed(expenses))[:8]
    return render_template("dashboard.html", stats=stats, recent=recent, active="dashboard")


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        name = request.form.get("expense_name", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", CATEGORIES[0])
        date = request.form.get("date", "").strip()

        is_valid, error, amount = validate_expense_form(name, amount_raw, date)

        if not is_valid:
            flash(error, "error")
            return render_template(
                "add.html", categories=CATEGORIES, active="add",
                form_values={"expense_name": name, "amount": amount_raw, "category": category, "date": date},
            )

        save_expense({"expense_name": name, "amount": amount, "category": category, "date": date})
        flash(f"'{name}' was added to your expenses.", "success")
        return redirect(url_for("add_expense"))

    today = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        "add.html", categories=CATEGORIES, active="add",
        form_values={"expense_name": "", "amount": "", "category": CATEGORIES[0], "date": today},
    )


@app.route("/expenses")
def all_expenses():
    expenses = list(reversed(load_expenses()))
    return render_template("expenses.html", expenses=expenses, active="all")


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    expense = get_expense(expense_id)
    if not expense:
        flash("Expense not found.", "error")
        return redirect(url_for("all_expenses"))

    if request.method == "POST":
        name = request.form.get("expense_name", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", CATEGORIES[0])
        date = request.form.get("date", "").strip()

        is_valid, error, amount = validate_expense_form(name, amount_raw, date)

        if not is_valid:
            flash(error, "error")
            expense.update({"expense_name": name, "amount": amount_raw, "category": category, "date": date})
            return render_template("edit.html", expense=expense, categories=CATEGORIES, active="all")

        update_expense(expense_id, name, amount, category, date)
        flash(f"'{name}' was updated successfully.", "success")
        return redirect(url_for("all_expenses"))

    return render_template("edit.html", expense=expense, categories=CATEGORIES, active="all")


@app.route("/expenses/<int:expense_id>/delete", methods=["POST"])
def delete_expense_route(expense_id):
    expense = get_expense(expense_id)
    delete_expense(expense_id)
    if expense:
        flash(f"'{expense['expense_name']}' was deleted.", "success")
    return redirect(url_for("all_expenses"))


@app.route("/charts")
def charts():
    expenses = load_expenses()
    stats = compute_stats(expenses)
    categories = list(stats["category_totals"].keys())
    values = list(stats["category_totals"].values())
    colors = [CATEGORY_COLORS.get(c, "#7C7C8A") for c in categories]

    months = sorted(stats["monthly_totals"].keys())
    month_values = [stats["monthly_totals"][m] for m in months]

    return render_template(
        "charts.html",
        active="charts",
        has_data=bool(expenses),
        categories=categories,
        values=values,
        colors=colors,
        months=months,
        month_values=month_values,
    )


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True, host="0.0.0.0", port=5000)
