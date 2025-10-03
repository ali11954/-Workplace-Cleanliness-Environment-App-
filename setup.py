# main.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    sites = db.relationship('Site', backref='location', lazy=True)

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    places = db.relationship('Place', backref='site', lazy=True)

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    criteria = db.relationship('Criteria', backref='place', lazy=True)

class Criteria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)

# Routes
@app.route('/')
def index():
    return redirect(url_for('criteria'))

@app.route('/criteria')
def criteria():
    locations = Location.query.all()
    return render_template('admin/criteria.html', locations=locations)

@app.route('/add_criteria', methods=['POST'])
def add_criteria():
    place_id = request.form.get('place_id')
    name = request.form.get('criteria_name')
    if place_id and name:
        criteria = Criteria(name=name, place_id=place_id)
        db.session.add(criteria)
        db.session.commit()
    return redirect(url_for('criteria'))

@app.route('/get_sites/<int:location_id>')
def get_sites(location_id):
    sites = Site.query.filter_by(location_id=location_id).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in sites])

@app.route('/get_places/<int:site_id>')
def get_places(site_id):
    places = Place.query.filter_by(site_id=site_id).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in places])

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
