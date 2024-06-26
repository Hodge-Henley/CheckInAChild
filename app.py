from flask import Flask, render_template, request, redirect, url_for
import os
import random
import string
from barcode import Code128
from barcode.writer import ImageWriter
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

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

    # Create child's ticket
    c = canvas.Canvas(f"static/tags/{unique_number}_child.pdf", pagesize=letter)
    c.drawString(100, 750, "Child's Ticket")
    c.drawString(100, 730, f"Child's Name: {child_name}")
    c.drawString(100, 710, f"Parent/Guardian's Name: {parent_name}")
    c.drawString(100, 690, f"Unique Number: {unique_number}")
    c.drawImage(f'static/barcodes/{unique_number}.png', 100, 600, width=2*inch, height=1*inch)
    c.save()

    # Create parent's ticket
    p = canvas.Canvas(f"static/tags/{unique_number}_parent.pdf", pagesize=letter)
    p.drawString(100, 750, "Parent's Ticket")
    p.drawString(100, 730, f"Child's Name: {child_name}")
    p.drawString(100, 710, f"Parent/Guardian's Name: {parent_name}")
    p.drawString(100, 690, f"Unique Number: {unique_number}")
    p.drawImage(f'static/barcodes/{unique_number}.png', 100, 600, width=2*inch, height=1*inch)
    p.save()

def create_directories():
    os.makedirs('static/barcodes', exist_ok=True)
    os.makedirs('static/tags', exist_ok=True)

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

    # Print tags
    print_tag(child_name, parent_name, unique_number)

    return redirect(url_for('confirmation', number=unique_number))

@app.route('/confirmation/<number>')
def confirmation(number):
    return render_template('confirmation.html', number=number)

@app.route('/print_labels/<number>')
def print_labels(number):
    conn = sqlite3.connect('checkin.db')
    c = conn.cursor()
    c.execute("SELECT child_name, parent_name FROM checkins WHERE unique_number=?", (number,))
    row = c.fetchone()
    conn.close()
    
    if row:
        child_name, parent_name = row
        return render_template('print_labels.html', number=number, child_name=child_name, parent_name=parent_name)
    else:
        return "Record not found", 404

if __name__ == '__main__':
    init_db()
    create_directories()
    app.run(debug=True)
