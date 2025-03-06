from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Vervang door een echte SMTP-server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_password'

mail = Mail(app)
db = SQLAlchemy(app)

# Database model
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    shift = db.Column(db.String(20), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Beschikbare kamers en shifts
rooms = {
    "Gebouw 7, verdieping 0": ["17", "15", "13", "11", "9", "7", "41", "47", "49", "51", "35"],
    "Gebouw 7, verdieping 1": ["119", "117", "113", "111", "109", "107", "105", "125", "127"],
    "Gebouw 27, verdieping 0": ["038", "037", "021", "027", "028", "058", "059", "064", "065", "048", "022"],
    "Gebouw 27, verdieping 1": ["1113", "1114", "1119", "1120", "1129", "1128"]
}
shifts = ["21:00-00:00", "00:15-03:15", "03:30-07:00"]
max_beds_per_shift = 50

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        shift = request.form['shift']
        room_number = request.form['room_number']
        
        shift_count = Reservation.query.filter_by(shift=shift).count()
        if shift_count >= max_beds_per_shift:
            flash("Deze shift is volgeboekt. Kies een andere shift.", "danger")
            return redirect(url_for('index'))
        
        reservation = Reservation(name=name, phone=phone, email=email, shift=shift, room_number=room_number)
        db.session.add(reservation)
        db.session.commit()
        
        if email:
            msg = Message('Bevestiging reservering', sender='your_email@example.com', recipients=[email])
            msg.body = f"Bedankt {name}, je hebt succesvol een bed gereserveerd in kamer {room_number} voor de shift {shift}."
            mail.send(msg)
        
        return redirect(url_for('confirmation', name=name, shift=shift, room_number=room_number))
    
    available_shifts = {shift: max_beds_per_shift - Reservation.query.filter_by(shift=shift).count() for shift in shifts}
    return render_template('index.html', shifts=shifts, rooms=rooms, available_shifts=available_shifts)

@app.route('/confirmation')
def confirmation():
    name = request.args.get('name')
    shift = request.args.get('shift')
    room_number = request.args.get('room_number')
    return render_template('confirmation.html', name=name, shift=shift, room_number=room_number)

@app.route('/admin')
def admin():
    reservations = Reservation.query.order_by(Reservation.timestamp.desc()).all()
    return render_template('admin.html', reservations=reservations)

@app.route('/cancel', methods=['GET'])
def cancel():
    name = request.args.get('name')
    shift = request.args.get('shift')
    reservation = Reservation.query.filter_by(name=name, shift=shift).first()
    if reservation:
        db.session.delete(reservation)
        db.session.commit()
        flash("Reservering geannuleerd.", "success")
        return redirect(url_for('index'))
    else:
        flash("Reservering niet gevonden.", "danger")
        return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
