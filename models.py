from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

user_regions = db.Table('user_regions',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('region_id', db.Integer, db.ForeignKey('location.id'), primary_key=True)
)
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150))
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # ← جديد
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)

    region_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    regions = db.relationship('Location', secondary=user_regions, backref='users')

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def is_active(self):
        # Flask-Login يتوقع خاصية is_active تعود True أو False
        return self.active


class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)

    sites = db.relationship('Site', backref='location', cascade='all, delete-orphan')
    children = db.relationship('Location')


class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    region_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

    # علاقة مع الأماكن (Places)
    places = db.relationship('Place', backref='site', cascade='all, delete-orphan')


class Place(db.Model):
    __tablename__ = 'place'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    criteria = db.relationship('Criterion', back_populates='place', cascade='all, delete-orphan')

    # علاقة مع المعايير (Criteria)


class Criterion(db.Model):
    __tablename__ = 'criterion'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    min_score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    authority_id = db.Column(db.Integer, db.ForeignKey('evaluation_authorities.id'))  # ✅ هذا جديد

    place = db.relationship('Place', back_populates='criteria')

    authority = db.relationship('EvaluationAuthority', backref='criteria')



class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_score = db.Column(db.Integer)
    percent = db.Column(db.Float)
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)


    # العلاقات
    region = db.relationship('Location', foreign_keys=[region_id], backref='evaluations')
    site = db.relationship('Site', backref=db.backref('evaluations', lazy=True))
    place = db.relationship('Place', backref=db.backref('evaluations', lazy=True))
    user = db.relationship('User', backref=db.backref('evaluations', lazy=True))
    criterion = db.relationship('Criterion', backref=db.backref('evaluations', lazy=True))
    details = db.relationship('EvaluationDetail', backref='evaluation', cascade='all, delete-orphan')


class EvaluationDetail(db.Model):
    __tablename__ = "evaluation_detail"   # ← لازم يتطابق مع foreign key
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # إضافة جهة المسؤولية
    authority_id = db.Column(db.Integer, db.ForeignKey('evaluation_authorities.id'), nullable=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=True)
    place = db.relationship('Place', backref='evaluation_details')

    # العلاقات
    note = db.Column(db.Text, nullable=True)

    criterion = db.relationship('Criterion', backref=db.backref('evaluation_details', cascade='all, delete-orphan'))
    user = db.relationship('User')
    authority = db.relationship('EvaluationAuthority', backref='evaluation_details')

class EvaluationAuthority(db.Model):
    __tablename__ = 'evaluation_authorities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<EvaluationAuthority {self.name}>"


from datetime import datetime



class ActionPlan(db.Model):
    __tablename__ = "action_plans"
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Text)
    plan_text = db.Column(db.Text)
    action_plan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed = db.Column(db.Boolean, default=False)
    closed_date = db.Column(db.DateTime, nullable=True)
    improvement_score = db.Column(db.Float, nullable=True)

    evaluation_detail_id = db.Column(db.Integer, db.ForeignKey("evaluation_detail.id"))
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey("site.id"), nullable=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=True)
    criterion_id = db.Column(db.Integer, db.ForeignKey("criterion.id"), nullable=True)

    # ✅ العلاقات
    evaluation_detail = db.relationship("EvaluationDetail", backref="action_plans")
    location = db.relationship("Location", backref="action_plans")
    site = db.relationship("Site", backref="action_plans")
    place = db.relationship("Place", backref="action_plans")
    criterion = db.relationship("Criterion", backref="action_plans")
    closing_note = db.Column(db.Text, nullable=True)
