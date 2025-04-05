from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import qrcode
import os
import datetime
import pandas as pd

app = Flask(__name__)
DB_FILE = 'database.db'
QR_FOLDER = 'static/qr'

# Ensure QR folder exists
os.makedirs(QR_FOLDER, exist_ok=True)

# Initialize DB
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            lecture_id TEXT,
            timestamp TEXT
        )
        ''')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        lecture_id = request.form['lecture_id']
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        qr_data = f"{lecture_id}|{timestamp}"
        img = qrcode.make(qr_data)
        qr_path = os.path.join(QR_FOLDER, f"{lecture_id}.png")
        img.save(qr_path)
        return render_template('show_qr.html', qr_path=qr_path)
    except Exception as e:
        return f"Error generating QR: {e}", 500

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    student_id = request.form['student_id']
    qr_data = request.form['qr_data']
    try:
        lecture_id, timestamp = qr_data.split('|')
    except ValueError:
        return "Invalid QR Data"
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO attendance (student_id, lecture_id, timestamp) VALUES (?, ?, ?)",
                    (student_id, lecture_id, timestamp))
    return "Attendance marked!"

@app.route('/view')
def view_attendance():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM attendance")
        records = cur.fetchall()
    return render_template('attendance.html', records=records)

@app.route('/export')
def export_csv():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        csv_path = os.path.join('static', 'attendance_report.csv')
        df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)

@app.route('/scan')
def scan():
    return render_template('scan.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)