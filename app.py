from flask import Flask, render_template, request, redirect, url_for
import random
import string
from barcode import Code128
from barcode.writer import ImageWriter
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('checkin.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS checkins
                 (id INTEGER PRIMARY KEY, child_name TEXT, parent_name TEXT, unique_number TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(child_name, parent_name, unique_number):
    conn = sqlite3.connect('checkin.db')
    c = conn.cursor()
    c.execute("INSERT INTO checkins (child_name, parent_name, unique_number) VALUES (?, ?, ?)",
              (child_name, parent_name, unique_number))
    conn.commit()
    conn.close()

def print_tag(child_name, parent_name, unique_number):
    c = canvas.Canvas(f"static/tags/{unique_number}.pdf", pagesize=letter)
    c.drawString(100, 750, f"Child's Name: {child_name}")
    c.drawString(100, 730, f"Parent/Guardian's Name: {parent_name}")
    c.drawString(100, 710, f"Unique Number: {unique_number}")
    c.drawImage(f'static/barcodes/{unique_number}.png', 100, 650, width=200, height=100)
    c.save()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/checkin', methods=['POST'])
def checkin():
    child_name = request.form['child_name']
    parent_name = request.form['parent_name']
    unique_number = ''.join(random.choices(string.digits, k=6))

    # Generate barcode
    barcode = Code128(unique_number, writer=ImageWriter())
    barcode.save(f'static/barcodes/{unique_number}')

    # Save data to database
    save_to_db(child_name, parent_name, unique_number)

    # Print tag
    print_tag(child_name, parent_name, unique_number)

    return redirect(url_for('confirmation', number=unique_number))

@app.route('/confirmation/<number>')
def confirmation(number):
    return render_template('confirmation.html', number=number)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
