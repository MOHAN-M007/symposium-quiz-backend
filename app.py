from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)
DB_FILE = "quiz.db"
ADMIN_KEY = "admin123"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team TEXT NOT NULL,
                        score INTEGER DEFAULT 0)''')
        conn.commit()

@app.route("/")
def home():
    return jsonify({"ok": True, "service": "Symposium Quiz Backend", "version": 1})

@app.route("/admin")
def admin():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "Unauthorized", 403
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, question, answer FROM questions")
        rows = cur.fetchall()
    return render_template("admin.html", questions=rows, key=ADMIN_KEY)

@app.route("/api/questions")
def api_questions():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, question FROM questions")
        data = [{"id": r[0], "question": r[1]} for r in cur.fetchall()]
    return jsonify(data)

@app.route("/api/submit", methods=["POST"])
def api_submit():
    data = request.get_json()
    team = data.get("team")
    qid = data.get("question")
    ans = data.get("answer", "").strip().lower()

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT answer FROM questions WHERE id=?", (qid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": False, "msg": "Invalid question"})
        correct = (row[0].lower() == ans)

        cur.execute("SELECT id, score FROM scores WHERE team=?", (team,))
        row2 = cur.fetchone()
        if row2:
            if correct:
                cur.execute("UPDATE scores SET score=score+1 WHERE id=?", (row2[0],))
        else:
            cur.execute("INSERT INTO scores (team, score) VALUES (?, ?)", (team, 1 if correct else 0))
        conn.commit()

    return jsonify({"ok": True, "correct": correct})

@app.route("/api/leaderboard")
def api_leaderboard():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT team, score FROM scores ORDER BY score DESC")
        data = [{"team": r[0], "score": r[1]} for r in cur.fetchall()]
    return jsonify(data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0")
