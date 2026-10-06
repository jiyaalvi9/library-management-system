import os
import sqlite3
from datetime import date, timedelta
from flask import Flask, jsonify, request, g

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "library.db")
app = Flask(__name__, static_folder=os.path.join(BASE, "..", "frontend"), static_url_path="")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        author TEXT NOT NULL, isbn TEXT, copies INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS members(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT);
    CREATE TABLE IF NOT EXISTS loans(
        id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL, issued TEXT NOT NULL, due TEXT NOT NULL, returned TEXT);
    """)
    c.commit()
    c.close()


def rows(q, a=()):
    return [dict(r) for r in db().execute(q, a).fetchall()]


def err(msg, code=400):
    return jsonify(error=msg), code


@app.route("/")
def index():
    return app.send_static_file("index.html")


# ---- Books ----
@app.get("/api/books")
def list_books():
    return jsonify(rows("""SELECT b.*, b.copies - (SELECT COUNT(*) FROM loans l
        WHERE l.book_id=b.id AND l.returned IS NULL) AS available FROM books b ORDER BY b.title"""))


@app.post("/api/books")
def add_book():
    d = request.get_json(silent=True) or {}
    if not d.get("title") or not d.get("author"):
        return err("title and author are required")
    copies = max(int(d.get("copies") or 1), 1)
    db().execute("INSERT INTO books(title,author,isbn,copies) VALUES(?,?,?,?)",
                 (d["title"].strip(), d["author"].strip(), d.get("isbn", ""), copies))
    db().commit()
    return jsonify(ok=True), 201


@app.delete("/api/books/<int:i>")
def delete_book(i):
    if rows("SELECT 1 FROM loans WHERE book_id=? AND returned IS NULL", (i,)):
        return err("book is currently on loan", 409)
    db().execute("DELETE FROM books WHERE id=?", (i,))
    db().commit()
    return jsonify(ok=True)


# ---- Members ----
@app.get("/api/members")
def list_members():
    return jsonify(rows("SELECT * FROM members ORDER BY name"))


@app.post("/api/members")
def add_member():
    d = request.get_json(silent=True) or {}
    if not d.get("name"):
        return err("name is required")
    db().execute("INSERT INTO members(name,email) VALUES(?,?)", (d["name"].strip(), d.get("email", "")))
    db().commit()
    return jsonify(ok=True), 201


@app.delete("/api/members/<int:i>")
def delete_member(i):
    if rows("SELECT 1 FROM loans WHERE member_id=? AND returned IS NULL", (i,)):
        return err("member has unreturned books", 409)
    db().execute("DELETE FROM members WHERE id=?", (i,))
    db().commit()
    return jsonify(ok=True)


# ---- Loans ----
@app.get("/api/loans")
def list_loans():
    return jsonify(rows("""SELECT l.*, b.title, m.name AS member FROM loans l
        JOIN books b ON b.id=l.book_id JOIN members m ON m.id=l.member_id
        ORDER BY l.returned IS NOT NULL, l.due"""))


@app.post("/api/loans")
def issue():
    d = request.get_json(silent=True) or {}
    b = rows("""SELECT b.copies - (SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id
        AND l.returned IS NULL) AS available FROM books b WHERE b.id=?""", (d.get("book_id"),))
    if not b:
        return err("book not found", 404)
    if b[0]["available"] < 1:
        return err("no copies available", 409)
    if not rows("SELECT 1 FROM members WHERE id=?", (d.get("member_id"),)):
        return err("member not found", 404)
    today = date.today()
    db().execute("INSERT INTO loans(book_id,member_id,issued,due) VALUES(?,?,?,?)",
                 (d["book_id"], d["member_id"], today.isoformat(), (today + timedelta(days=14)).isoformat()))
    db().commit()
    return jsonify(ok=True), 201


@app.post("/api/loans/<int:i>/return")
def return_book(i):
    db().execute("UPDATE loans SET returned=? WHERE id=? AND returned IS NULL", (date.today().isoformat(), i))
    db().commit()
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
