from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here_change_it'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evaluations.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Models

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20))  # admin / user
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    parent = db.relationship('Location', remote_side=[id], backref='children')


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    cleanliness = db.Column(db.Integer, nullable=False)
    ventilation = db.Column(db.Integer, nullable=False)
    lighting = db.Column(db.Integer, nullable=False)
    safety = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    location = db.relationship('Location')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# دالة مساعدة لبناء خيارات شجرية في قائمة اختيار HTML
def get_location_options(locations, parent_id=None, level=0):
    html = ""
    filtered = [loc for loc in locations if loc.parent_id == parent_id]
    prefix = "— " * level
    for loc in filtered:
        html += f'<option value="{loc.id}">{prefix}{loc.name}</option>'
        html += get_location_options(locations, loc.id, level + 1)
    return html


# Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('admin/templates/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    locations = Location.query.filter_by(parent_id=None).all()  # المواقع الرئيسية فقط للعرض
    return render_template('user/dashboard.html', locations=locations)


@app.route('/add_location', methods=['GET', 'POST'])
@login_required
def add_location():
    if request.method == 'POST':
        name = request.form['name']
        parent_id = request.form.get('parent_id') or None
        if parent_id == '':
            parent_id = None

        existing = Location.query.filter_by(name=name, parent_id=parent_id).first()
        if existing:
            flash('الموقع موجود مسبقًا تحت نفس التصنيف', 'warning')
        else:
            loc = Location(name=name, parent_id=parent_id)
            db.session.add(loc)
            db.session.commit()
            flash('تم إضافة الموقع', 'success')
            return redirect(url_for('dashboard'))

    # GET request
    locations = Location.query.all()
    location_options = get_location_options(locations)
    return render_template('admin/locations.html', location_options=location_options)


@app.route('/evaluate', methods=['GET', 'POST'])
@login_required
def evaluate():
    locations = Location.query.all()
    location_options = get_location_options(locations)
    if request.method == 'POST':
        location_id = request.form['location']
        cleanliness = int(request.form['cleanliness'])
        ventilation = int(request.form['ventilation'])
        lighting = int(request.form['lighting'])
        safety = int(request.form['safety'])
        notes = request.form['notes']

        eval = Evaluation(location_id=location_id, cleanliness=cleanliness,
                          ventilation=ventilation, lighting=lighting,
                          safety=safety, notes=notes)
        db.session.add(eval)
        db.session.commit()
        flash('تم حفظ التقييم', 'success')
        return redirect(url_for('dashboard'))

    return render_template('user/evaluate.html', location_options=location_options)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # إنشاء مستخدم تجريبي admin إذا لم يكن موجودًا
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
